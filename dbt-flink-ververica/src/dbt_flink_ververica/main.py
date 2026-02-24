"""Main CLI entry point for dbt-flink-ververica.

This module provides the Typer-based CLI interface for compiling dbt projects
and deploying them to Ververica Cloud.
"""

import logging
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.logging import RichHandler

from . import __version__


# Initialize Rich console for beautiful output
console = Console()

# Initialize Typer app
app = typer.Typer(
    name="dbt-flink-ververica",
    help="CLI tool for deploying dbt-flink projects to Ververica Cloud",
    add_completion=True,
    rich_markup_mode="rich",
)

# Configure logging with Rich
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger(__name__)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"dbt-flink-ververica version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose logging",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        help="Suppress non-error output",
    ),
) -> None:
    """dbt-flink-ververica: Deploy dbt-flink projects to Ververica Cloud.

    This tool compiles dbt models to Flink SQL and deploys them to Ververica Cloud
    as SQLSCRIPT jobs (Phase 1) or JAR packages (Phase 2, future).

    Common workflows:

      • Login: dbt-flink-ververica auth login
      • Compile: dbt-flink-ververica compile
      • Deploy: dbt-flink-ververica deploy --name my-job
      • Full workflow: dbt-flink-ververica workflow --name my-job
    """
    # Configure log level based on flags
    if quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)


# ============================================================================
# Auth Commands
# ============================================================================

auth_app = typer.Typer(
    name="auth",
    help="Manage Ververica Cloud authentication",
)
app.add_typer(auth_app)


@auth_app.command("login")
def auth_login(
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        prompt=True,
        help="Ververica Cloud email address",
    ),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        help="Ververica Cloud password",
    ),
    gateway_url: str = typer.Option(
        "https://app.ververica.cloud",
        "--gateway-url",
        help="Ververica Cloud gateway URL",
    ),
    no_save: bool = typer.Option(
        False,
        "--no-save",
        help="Don't save credentials to system keyring",
    ),
) -> None:
    """Login to Ververica Cloud and save credentials.

    Credentials are securely stored in your system keyring (macOS Keychain,
    Windows Credential Manager, Linux Secret Service).
    """
    from .auth import AuthManager

    try:
        auth_manager = AuthManager(gateway_url)
        token = auth_manager.login(
            email=email,
            password=password,
            save_credentials=not no_save
        )

        console.print("[green]✓[/green] Authentication successful!")
        console.print(f"Token expires at: {token.expires_at.isoformat()}")

        if not no_save:
            console.print("[green]✓[/green] Credentials saved to system keyring")

    except Exception as e:
        console.print(f"[red]✗[/red] Authentication failed: {e}")
        raise typer.Exit(code=1)


@auth_app.command("logout")
def auth_logout(
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        prompt=True,
        help="Ververica Cloud email address",
    ),
    keep_credentials: bool = typer.Option(
        False,
        "--keep-credentials",
        help="Keep saved credentials in keyring",
    ),
    gateway_url: str = typer.Option(
        "https://app.ververica.cloud",
        "--gateway-url",
        help="Ververica Cloud gateway URL",
    ),
) -> None:
    """Logout and optionally delete saved credentials."""
    from .auth import AuthManager

    try:
        auth_manager = AuthManager(gateway_url)
        auth_manager.logout(
            email=email,
            delete_credentials=not keep_credentials
        )

        console.print("[green]✓[/green] Logged out successfully")

        if not keep_credentials:
            console.print("[green]✓[/green] Credentials deleted from system keyring")

    except Exception as e:
        console.print(f"[red]✗[/red] Logout failed: {e}")
        raise typer.Exit(code=1)


@auth_app.command("status")
def auth_status(
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        prompt=True,
        help="Ververica Cloud email address",
    ),
) -> None:
    """Check if credentials are saved for a user."""
    from .auth import CredentialManager

    credentials = CredentialManager.get_credentials(email)

    if credentials is not None:
        console.print(f"[green]✓[/green] Credentials found for: {email}")
    else:
        console.print(f"[yellow]![/yellow] No credentials found for: {email}")
        console.print("Run 'dbt-flink-ververica auth login' to save credentials")


# ============================================================================
# Compile Commands
# ============================================================================

@app.command("compile")
def compile_command(
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        help="Path to dbt project directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    profiles_dir: Optional[Path] = typer.Option(
        None,
        "--profiles-dir",
        help="Path to dbt profiles directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    target: str = typer.Option(
        "dev",
        "--target",
        "-t",
        help="dbt target to use for compilation",
    ),
    models: Optional[str] = typer.Option(
        None,
        "--models",
        "-m",
        help="Specific models to compile (comma-separated)",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Output directory for compiled SQL (default: target/run)",
    ),
) -> None:
    """Compile dbt models to Flink SQL.

    This runs 'dbt compile' and extracts the compiled SQL from the target/run directory.
    The SQL is transformed to be compatible with Ververica Cloud deployment.
    """
    import subprocess
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from .sql_processor import DbtArtifactReader, SqlProcessor

    console.print("[blue]ℹ[/blue] Compiling dbt project...")
    console.print(f"Project: {project_dir}")
    console.print(f"Target: {target}")
    console.print()

    # Parse model list
    model_list = None
    if models:
        model_list = [m.strip() for m in models.split(",")]
        console.print(f"Models: {', '.join(model_list)}")
    else:
        console.print("Models: all")

    # Set output directory
    if output_dir is None:
        output_dir = project_dir / "target" / "ververica"
    console.print(f"Output: {output_dir}")
    console.print()

    try:
        # Step 1: Run dbt compile
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running dbt compile...", total=None)

            # Build dbt command
            dbt_cmd = ["dbt", "compile", "--target", target]
            if profiles_dir:
                dbt_cmd.extend(["--profiles-dir", str(profiles_dir)])
            if models:
                dbt_cmd.extend(["--models", models])

            logger.debug(f"Running: {' '.join(dbt_cmd)}")

            # Run dbt compile
            try:
                result = subprocess.run(
                    dbt_cmd,
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )
            except subprocess.TimeoutExpired:
                progress.update(task, completed=True)
                console.print("[red]✗[/red] dbt compile timed out after 5 minutes")
                raise typer.Exit(code=1)
            except FileNotFoundError:
                progress.update(task, completed=True)
                console.print("[red]✗[/red] dbt command not found. Is dbt installed?")
                console.print("Install with: pip install dbt-flink")
                raise typer.Exit(code=1)
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗[/red] Failed to run dbt compile: {e}")
                raise typer.Exit(code=1)

            progress.update(task, completed=True)

            if result.returncode != 0:
                console.print("[red]✗[/red] dbt compile failed")
                console.print(result.stderr)
                raise typer.Exit(code=1)

            console.print("[green]✓[/green] dbt compile successful")
            console.print()

        # Step 2: Read compiled models
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Reading compiled models...", total=None)

            reader = DbtArtifactReader(project_dir, target)
            compiled_models = reader.find_compiled_models(model_list)

            progress.update(task, completed=True)

            if not compiled_models:
                console.print("[yellow]![/yellow] No compiled models found")
                raise typer.Exit(code=0)

            console.print(f"[green]✓[/green] Found {len(compiled_models)} compiled models")
            console.print()

        # Step 3: Process SQL
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Processing SQL...", total=len(compiled_models))

            processor = SqlProcessor(
                strip_hints=True,
                generate_set_statements=True,
                include_drop_statements=True,
                wrap_in_statement_set=False,
            )

            processed_models = reader.process_models(compiled_models, processor)

            for model in processed_models:
                progress.update(task, advance=1)

            console.print(f"[green]✓[/green] Processed {len(processed_models)} models")
            console.print()

        # Step 4: Write output files
        console.print(f"Writing processed SQL to: {output_dir}")
        console.print()

        for model in processed_models:
            output_file = reader.write_processed_sql(model, output_dir)
            console.print(f"  [green]✓[/green] {model.name}.sql")

            # Show summary of transformations
            if model.processed:
                hint_count = len(model.processed.hints)
                set_count = len(model.processed.set_statements)
                drop_count = len(model.processed.drop_statements)

                if hint_count > 0:
                    console.print(f"    • Parsed {hint_count} hints")
                if set_count > 0:
                    console.print(f"    • Generated {set_count} SET statements")
                if drop_count > 0:
                    console.print(f"    • Extracted {drop_count} DROP statements")

        console.print()
        console.print("[green]✓[/green] Compilation complete!")
        console.print()
        console.print(f"Next steps:")
        console.print(f"  • Review SQL in: {output_dir}")
        console.print(f"  • Deploy with: dbt-flink-ververica deploy --name <deployment-name>")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗[/red] Compilation failed: {e}")
        logger.exception("Compilation error")
        raise typer.Exit(code=1)


# ============================================================================
# Helpers
# ============================================================================

def _load_config(config_file: Optional[Path]) -> Optional["ToolConfig"]:
    """Load TOML config with fallback to default location.

    Priority:
    1. Explicit --config path
    2. dbt-flink-ververica.toml in current working directory
    3. None (no config)

    Args:
        config_file: Explicit path to config file, or None for auto-discovery

    Returns:
        Parsed ToolConfig, or None if no config found
    """
    from .config import ToolConfig

    if config_file is not None:
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        logger.debug(f"Loading config from explicit path: {config_file}")
        return ToolConfig.from_toml(config_file)

    default_path = Path.cwd() / "dbt-flink-ververica.toml"
    if default_path.exists():
        logger.debug(f"Loading config from default path: {default_path}")
        return ToolConfig.from_toml(default_path)

    logger.debug("No config file found")
    return None


def _resolve_auth(
    gateway_url: str,
    email: str,
    password: Optional[str],
) -> "AuthToken":
    """Resolve authentication using password or keyring.

    Priority:
    1. Explicit password (from --password flag or VERVERICA_PASSWORD env var)
    2. Saved credentials in system keyring

    Args:
        gateway_url: Ververica Cloud gateway URL
        email: User email
        password: Explicit password, or None to use keyring

    Returns:
        Valid AuthToken

    Raises:
        ValueError: If no password and no saved credentials
    """
    from .auth import AuthManager

    auth_manager = AuthManager(gateway_url)
    return auth_manager.get_valid_token(email, password=password)


# ============================================================================
# Deploy Commands
# ============================================================================

@app.command("deploy")
def deploy_command(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Deployment name",
    ),
    sql_file: Optional[Path] = typer.Option(
        None,
        "--sql-file",
        help="Path to SQL file to deploy (default: auto-discover from target/ververica/)",
    ),
    workspace_id: str = typer.Option(
        ...,
        "--workspace-id",
        envvar="VERVERICA_WORKSPACE_ID",
        help="Ververica workspace ID",
    ),
    namespace: str = typer.Option(
        "default",
        "--namespace",
        envvar="VERVERICA_NAMESPACE",
        help="Ververica namespace",
    ),
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        envvar="VERVERICA_EMAIL",
        help="Ververica Cloud email (for authentication)",
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        envvar="VERVERICA_PASSWORD",
        help="Ververica Cloud password (for CI/CD; skips keyring)",
    ),
    gateway_url: str = typer.Option(
        "https://app.ververica.cloud",
        "--gateway-url",
        envvar="VERVERICA_GATEWAY_URL",
        help="Ververica Cloud gateway URL",
    ),
    parallelism: int = typer.Option(
        1,
        "--parallelism",
        help="Job parallelism",
        min=1,
        max=1000,
    ),
    engine_version: str = typer.Option(
        "vera-4.0.0-flink-1.20",
        "--engine-version",
        envvar="VERVERICA_ENGINE_VERSION",
        help="Flink engine version",
    ),
    start: bool = typer.Option(
        False,
        "--start",
        help="Auto-start the deployment after creation",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        help="Path to dbt project directory (for auto-discovery of compiled SQL)",
    ),
) -> None:
    """Deploy SQL to Ververica Cloud.

    Creates a SQLSCRIPT deployment in Ververica Cloud. If --sql-file is not
    provided, auto-discovers compiled SQL from target/ververica/{name}.sql.
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from .client import VervericaClient, DeploymentSpec

    console.print("[blue]i[/blue] Deploying to Ververica Cloud...")
    console.print(f"Deployment name: {name}")
    console.print(f"Workspace: {workspace_id}")
    console.print(f"Namespace: {namespace}")
    console.print()

    try:
        # Step 1: Resolve SQL content
        if sql_file is not None:
            if not sql_file.exists():
                console.print(f"[red]x[/red] SQL file not found: {sql_file}")
                raise typer.Exit(code=1)
            console.print(f"Reading SQL from: {sql_file}")
            sql_content = sql_file.read_text(encoding='utf-8')
        else:
            # Auto-discover from target/ververica/
            auto_path = project_dir / "target" / "ververica" / f"{name}.sql"
            if auto_path.exists():
                console.print(f"Auto-discovered SQL: {auto_path}")
                sql_content = auto_path.read_text(encoding='utf-8')
            else:
                console.print("[red]x[/red] No SQL file specified and auto-discovery failed")
                console.print(f"  Looked for: {auto_path}")
                console.print("  Use --sql-file to specify a SQL file, or run 'compile' first")
                raise typer.Exit(code=1)

        console.print(f"[green]v[/green] Read {len(sql_content)} characters")
        console.print()

        # Step 2: Authenticate
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Authenticating...", total=None)
            token = _resolve_auth(gateway_url, email, password)
            progress.update(task, completed=True)

        console.print(f"[green]v[/green] Authenticated as {email}")
        console.print()

        # Step 3: Create deployment
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating deployment...", total=None)

            spec = DeploymentSpec(
                name=name,
                namespace=namespace,
                sql_script=sql_content,
                engine_version=engine_version,
                parallelism=parallelism,
            )

            with VervericaClient(gateway_url, workspace_id, token) as client:
                status = client.create_sqlscript_deployment(spec)

                # Step 4: Start if requested
                if start:
                    progress.update(task, description="Starting deployment...")
                    client.start_deployment(
                        namespace=namespace,
                        deployment_id=status.deployment_id,
                    )

            progress.update(task, completed=True)

        console.print(f"[green]v[/green] Deployment created successfully!")
        if start:
            console.print(f"[green]v[/green] Deployment starting...")
        console.print()
        console.print(f"Deployment details:")
        console.print(f"  - ID: {status.deployment_id}")
        console.print(f"  - Name: {status.name}")
        console.print(f"  - State: {status.state}")
        console.print(f"  - Engine: {engine_version}")
        console.print(f"  - Namespace: {namespace}")
        console.print()
        console.print(f"View in Ververica Cloud:")
        console.print(f"  {gateway_url}/workspaces/{workspace_id}/deployments/{status.deployment_id}")

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        console.print(f"[red]x[/red] File not found: {e}")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]x[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]x[/red] Deployment failed: {e}")
        logger.exception("Deployment error")
        raise typer.Exit(code=1)


# ============================================================================
# Workflow Commands
# ============================================================================

@app.command("workflow")
def workflow_command(
    name_prefix: str = typer.Option(
        ...,
        "--name-prefix",
        "-n",
        help="Deployment name prefix (each model becomes {prefix}-{model_name})",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        help="Path to dbt project directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    profiles_dir: Optional[Path] = typer.Option(
        None,
        "--profiles-dir",
        help="Path to dbt profiles directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    target: str = typer.Option(
        "dev",
        "--target",
        "-t",
        help="dbt target to use for compilation",
    ),
    models: Optional[str] = typer.Option(
        None,
        "--models",
        "-m",
        help="Specific models to deploy (comma-separated)",
    ),
    workspace_id: Optional[str] = typer.Option(
        None,
        "--workspace-id",
        envvar="VERVERICA_WORKSPACE_ID",
        help="Ververica workspace ID",
    ),
    namespace: str = typer.Option(
        "default",
        "--namespace",
        envvar="VERVERICA_NAMESPACE",
        help="Ververica namespace",
    ),
    email: Optional[str] = typer.Option(
        None,
        "--email",
        "-e",
        envvar="VERVERICA_EMAIL",
        help="Ververica Cloud email",
    ),
    password: Optional[str] = typer.Option(
        None,
        "--password",
        "-p",
        envvar="VERVERICA_PASSWORD",
        help="Ververica Cloud password (for CI/CD; skips keyring)",
    ),
    gateway_url: Optional[str] = typer.Option(
        None,
        "--gateway-url",
        envvar="VERVERICA_GATEWAY_URL",
        help="Ververica Cloud gateway URL",
    ),
    parallelism: int = typer.Option(
        1,
        "--parallelism",
        help="Job parallelism",
        min=1,
        max=1000,
    ),
    engine_version: Optional[str] = typer.Option(
        None,
        "--engine-version",
        envvar="VERVERICA_ENGINE_VERSION",
        help="Flink engine version (e.g. vera-4.0.0-flink-1.20)",
    ),
    start: bool = typer.Option(
        False,
        "--start",
        help="Auto-start deployments after creation",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Compile and show SQL without deploying",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to TOML config file for defaults",
    ),
) -> None:
    """Run complete workflow: compile, transform, authenticate, deploy per-model.

    Each dbt model becomes its own Ververica SQLSCRIPT deployment, named
    {name-prefix}-{model_name}. This matches VVC's model where one SQLSCRIPT
    deployment = one Flink job.

    Config priority: CLI flags > env vars > TOML config > defaults.
    """
    import subprocess
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from .sql_processor import DbtArtifactReader, SqlProcessor
    from .client import VervericaClient, DeploymentSpec

    try:
        # ── Step 0: Load config & merge defaults ──────────────────────
        config = _load_config(config_file)

        if config is not None:
            console.print(f"[blue]i[/blue] Loaded config: {config_file or 'dbt-flink-ververica.toml'}")

        # Merge: CLI flag > env var (handled by typer envvar) > TOML > hardcoded default
        if gateway_url is None:
            gateway_url = config.ververica.gateway_url if config else "https://app.ververica.cloud"
        if workspace_id is None:
            workspace_id = config.ververica.workspace_id if config else None
        if engine_version is None:
            engine_version = (
                config.ververica.default_engine_version
                if config
                else "vera-4.0.0-flink-1.20"
            )

        # Validate required fields (not needed for dry-run)
        if not dry_run:
            if not email:
                console.print("[red]x[/red] --email is required (or set VERVERICA_EMAIL)")
                raise typer.Exit(code=1)
            if not workspace_id:
                console.print("[red]x[/red] --workspace-id is required (or set VERVERICA_WORKSPACE_ID)")
                raise typer.Exit(code=1)

        # Parse model selector
        model_list = None
        if models:
            model_list = [m.strip() for m in models.split(",")]

        console.print()
        console.print("[bold]Step 1/5: Compile dbt models[/bold]")

        # ── Step 1: Compile ───────────────────────────────────────────
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running dbt compile...", total=None)

            dbt_cmd = ["dbt", "compile", "--target", target]
            if profiles_dir:
                dbt_cmd.extend(["--profiles-dir", str(profiles_dir)])
            if models:
                dbt_cmd.extend(["--models", models])

            logger.debug(f"Running: {' '.join(dbt_cmd)}")

            try:
                result = subprocess.run(
                    dbt_cmd,
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
            except subprocess.TimeoutExpired:
                progress.update(task, completed=True)
                console.print("[red]x[/red] dbt compile timed out after 5 minutes")
                raise typer.Exit(code=1)
            except FileNotFoundError:
                progress.update(task, completed=True)
                console.print("[red]x[/red] dbt command not found. Is dbt installed?")
                raise typer.Exit(code=1)
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]x[/red] Failed to run dbt compile: {e}")
                raise typer.Exit(code=1)

            progress.update(task, completed=True)

            if result.returncode != 0:
                console.print("[red]x[/red] dbt compile failed")
                console.print(result.stderr)
                raise typer.Exit(code=1)

        console.print("[green]v[/green] dbt compile successful")
        console.print()

        # ── Step 2: Transform ─────────────────────────────────────────
        console.print("[bold]Step 2/5: Process SQL[/bold]")

        reader = DbtArtifactReader(project_dir, target)
        compiled_models = reader.find_compiled_models(model_list)

        if not compiled_models:
            console.print("[yellow]![/yellow] No compiled models found")
            raise typer.Exit(code=0)

        processor = SqlProcessor(
            strip_hints=True,
            generate_set_statements=True,
            include_drop_statements=True,
            wrap_in_statement_set=False,
        )

        processed_models = reader.process_models(compiled_models, processor)

        for model in processed_models:
            hint_count = len(model.processed.hints) if model.processed else 0
            set_count = len(model.processed.set_statements) if model.processed else 0
            console.print(
                f"  [green]v[/green] {model.name}: "
                f"{hint_count} hints -> {set_count} SET statements"
            )

        console.print()

        # Write processed SQL to target/ververica/ for reference
        output_dir = project_dir / "target" / "ververica"
        for model in processed_models:
            reader.write_processed_sql(model, output_dir)

        # ── Dry-run exit ──────────────────────────────────────────────
        if dry_run:
            console.print("[bold]-- DRY RUN: showing processed SQL --[/bold]")
            console.print()

            for model in processed_models:
                if model.processed:
                    deployment_name = f"{name_prefix}-{model.name}"
                    console.print(f"[bold cyan]{deployment_name}[/bold cyan]")
                    console.print(model.processed.final_sql)
                    console.print()

            console.print(f"[green]v[/green] Dry run complete. {len(processed_models)} models processed.")
            console.print(f"SQL written to: {output_dir}")
            raise typer.Exit(code=0)

        # ── Step 3: Authenticate ──────────────────────────────────────
        console.print("[bold]Step 3/5: Authenticate[/bold]")

        token = _resolve_auth(gateway_url, email, password)

        console.print(f"[green]v[/green] Authenticated as {email}")
        console.print()

        # ── Step 4: Deploy per-model ──────────────────────────────────
        console.print("[bold]Step 4/5: Deploy to Ververica Cloud[/bold]")

        deployed = []

        with VervericaClient(gateway_url, workspace_id, token) as client:
            for model in processed_models:
                if not model.processed:
                    continue

                deployment_name = f"{name_prefix}-{model.name}"

                spec = DeploymentSpec(
                    name=deployment_name,
                    namespace=namespace,
                    sql_script=model.processed.final_sql,
                    engine_version=engine_version,
                    parallelism=parallelism,
                )

                status = client.create_sqlscript_deployment(spec)
                deployed.append(status)
                console.print(
                    f"  [green]v[/green] {deployment_name} -> "
                    f"{status.deployment_id} [CREATED]"
                )

            console.print()

            # ── Step 5: Start jobs (optional) ─────────────────────────
            if start:
                console.print("[bold]Step 5/5: Start jobs[/bold]")

                for status in deployed:
                    client.start_deployment(
                        namespace=namespace,
                        deployment_id=status.deployment_id,
                    )
                    console.print(
                        f"  [green]v[/green] {status.name} -> STARTING"
                    )

                console.print()
            else:
                console.print("[bold]Step 5/5: Start jobs[/bold]")
                console.print("  [yellow]![/yellow] Skipped (use --start to auto-start)")
                console.print()

        # ── Summary ───────────────────────────────────────────────────
        summary_table = Table(title="Workflow Summary")
        summary_table.add_column("Model", style="cyan")
        summary_table.add_column("Deployment ID")
        summary_table.add_column("Status", style="green")

        for status in deployed:
            state = "STARTING" if start else "CREATED"
            summary_table.add_row(status.name, status.deployment_id, state)

        console.print(summary_table)
        console.print()
        console.print(f"Deployed: {len(deployed)} models")
        if start:
            console.print(f"Started: {len(deployed)} jobs")
        console.print(
            f"View: {gateway_url}/workspaces/{workspace_id}/"
        )

    except typer.Exit:
        raise
    except FileNotFoundError as e:
        console.print(f"[red]x[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]x[/red] Workflow failed: {e}")
        logger.exception("Workflow error")
        raise typer.Exit(code=1)


# ============================================================================
# Config Commands
# ============================================================================

config_app = typer.Typer(
    name="config",
    help="Manage configuration files",
)
app.add_typer(config_app)


@config_app.command("init")
def config_init(
    output_path: Path = typer.Option(
        Path.cwd() / "dbt-flink-ververica.toml",
        "--output",
        "-o",
        help="Output path for config file",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite existing config file",
    ),
) -> None:
    """Initialize a new configuration file.

    Creates a dbt-flink-ververica.toml file with default settings
    that can be customized for your project.
    """
    from .config import ToolConfig

    if output_path.exists() and not force:
        console.print(f"[red]✗[/red] Config file already exists: {output_path}")
        console.print("Use --force to overwrite")
        raise typer.Exit(code=1)

    try:
        # Create default config
        config = ToolConfig()

        # Save to file
        config.to_toml(output_path)

        console.print(f"[green]✓[/green] Created config file: {output_path}")
        console.print("\nEdit this file to customize settings for your project")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to create config file: {e}")
        raise typer.Exit(code=1)


@config_app.command("validate")
def config_validate(
    config_path: Path = typer.Argument(
        ...,
        help="Path to config file to validate",
        exists=True,
    ),
) -> None:
    """Validate a configuration file.

    Checks that the TOML file is valid and all required fields are present.
    """
    from .config import ToolConfig

    try:
        config = ToolConfig.from_toml(config_path)
        console.print(f"[green]✓[/green] Config file is valid: {config_path}")

        # Show summary
        console.print("\n[bold]Configuration summary:[/bold]")
        console.print(f"  Ververica gateway: {config.ververica.gateway_url}")
        console.print(f"  Workspace ID: {config.ververica.workspace_id or '(not set)'}")
        console.print(f"  Namespace: {config.ververica.namespace}")
        console.print(f"  dbt project: {config.dbt.project_dir}")
        console.print(f"  dbt target: {config.dbt.target}")

    except Exception as e:
        console.print(f"[red]✗[/red] Config file is invalid: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
