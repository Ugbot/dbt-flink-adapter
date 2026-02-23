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
        help="Path to SQL file to deploy (default: use compiled dbt SQL)",
        exists=True,
    ),
    workspace_id: str = typer.Option(
        ...,
        "--workspace-id",
        help="Ververica workspace ID",
    ),
    namespace: str = typer.Option(
        "default",
        "--namespace",
        help="Ververica namespace",
    ),
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        help="Ververica Cloud email (for authentication)",
    ),
    gateway_url: str = typer.Option(
        "https://app.ververica.cloud",
        "--gateway-url",
        help="Ververica Cloud gateway URL",
    ),
    parallelism: int = typer.Option(
        1,
        "--parallelism",
        help="Job parallelism",
    ),
) -> None:
    """Deploy SQL to Ververica Cloud.

    This creates a SQLSCRIPT deployment in Ververica Cloud with the compiled SQL.
    Authentication credentials must be saved first (use 'auth login').
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from .auth import AuthManager
    from .client import VervericaClient, DeploymentSpec

    console.print("[blue]ℹ[/blue] Deploying to Ververica Cloud...")
    console.print(f"Deployment name: {name}")
    console.print(f"Workspace: {workspace_id}")
    console.print(f"Namespace: {namespace}")
    console.print()

    try:
        # Step 1: Read SQL file
        if sql_file is None:
            console.print("[red]✗[/red] No SQL file specified")
            console.print("Use --sql-file to specify a SQL file to deploy")
            console.print("Or run 'compile' first and this will deploy the compiled SQL")
            raise typer.Exit(code=1)

        console.print(f"Reading SQL from: {sql_file}")
        sql_content = sql_file.read_text(encoding='utf-8')
        console.print(f"[green]✓[/green] Read {len(sql_content)} characters")
        console.print()

        # Step 2: Authenticate
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Authenticating...", total=None)

            auth_manager = AuthManager(gateway_url)
            token = auth_manager.get_valid_token(email)

            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Authenticated as {email}")
        console.print()

        # Step 3: Create deployment
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating deployment...", total=None)

            # Build deployment spec
            spec = DeploymentSpec(
                name=name,
                namespace=namespace,
                sql_script=sql_content,
                parallelism=parallelism,
            )

            # Create deployment
            with VervericaClient(gateway_url, workspace_id, token) as client:
                status = client.create_sqlscript_deployment(spec)

            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Deployment created successfully!")
        console.print()
        console.print(f"Deployment details:")
        console.print(f"  • ID: {status.deployment_id}")
        console.print(f"  • Name: {status.name}")
        console.print(f"  • State: {status.state}")
        console.print(f"  • Namespace: {namespace}")
        console.print()
        console.print(f"View in Ververica Cloud:")
        console.print(f"  {gateway_url}/workspaces/{workspace_id}/deployments/{status.deployment_id}")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] File not found: {e}")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗[/red] Deployment failed: {e}")
        logger.exception("Deployment error")
        raise typer.Exit(code=1)


# ============================================================================
# Workflow Commands
# ============================================================================

@app.command("workflow")
def workflow_command(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Deployment name",
    ),
    project_dir: Path = typer.Option(
        Path.cwd(),
        "--project-dir",
        help="Path to dbt project directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    workspace_id: str = typer.Option(
        ...,
        "--workspace-id",
        help="Ververica workspace ID",
    ),
    namespace: str = typer.Option(
        "default",
        "--namespace",
        help="Ververica namespace",
    ),
    email: str = typer.Option(
        ...,
        "--email",
        "-e",
        help="Ververica Cloud email",
    ),
    target: str = typer.Option(
        "dev",
        "--target",
        "-t",
        help="dbt target",
    ),
) -> None:
    """Run complete workflow: compile + deploy.

    This is a convenience command that runs 'compile' followed by 'deploy'
    in a single operation.
    """
    import subprocess
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from .sql_processor import DbtArtifactReader, SqlProcessor
    from .auth import AuthManager
    from .client import VervericaClient, DeploymentSpec

    console.print("[blue]ℹ[/blue] Running full workflow (compile + deploy)...")
    console.print()

    try:
        # Step 1: Run dbt compile
        console.print("[bold]Step 1: Compile dbt models[/bold]")
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running dbt compile...", total=None)

            dbt_cmd = ["dbt", "compile", "--target", target]

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

        # Step 2: Read and process models
        console.print("[bold]Step 2: Process SQL[/bold]")
        console.print()

        reader = DbtArtifactReader(project_dir, target)
        compiled_models = reader.find_compiled_models()

        if not compiled_models:
            console.print("[yellow]![/yellow] No compiled models found")
            raise typer.Exit(code=0)

        console.print(f"Found {len(compiled_models)} models")

        processor = SqlProcessor(
            strip_hints=True,
            generate_set_statements=True,
            include_drop_statements=True,
            wrap_in_statement_set=False,
        )

        processed_models = reader.process_models(compiled_models, processor)
        console.print(f"[green]✓[/green] Processed {len(processed_models)} models")
        console.print()

        # Step 3: Combine SQL
        console.print("[bold]Step 3: Combine SQL[/bold]")
        console.print()

        combined_sql_parts = []
        combined_sql_parts.append("-- Combined SQL from dbt-flink models")
        combined_sql_parts.append(f"-- Generated: {target}")
        combined_sql_parts.append(f"-- Models: {len(processed_models)}")
        combined_sql_parts.append("")

        for model in processed_models:
            if model.processed:
                combined_sql_parts.append(f"-- Model: {model.name}")
                combined_sql_parts.append(model.processed.final_sql)
                combined_sql_parts.append("")
                combined_sql_parts.append("-- " + "-" * 70)
                combined_sql_parts.append("")

        combined_sql = "\n".join(combined_sql_parts)
        console.print(f"[green]✓[/green] Combined SQL: {len(combined_sql)} characters")
        console.print()

        # Step 4: Authenticate
        console.print("[bold]Step 4: Authenticate[/bold]")
        console.print()

        auth_manager = AuthManager("https://app.ververica.cloud")
        token = auth_manager.get_valid_token(email)

        console.print(f"[green]✓[/green] Authenticated as {email}")
        console.print()

        # Step 5: Deploy
        console.print("[bold]Step 5: Deploy to Ververica Cloud[/bold]")
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating deployment...", total=None)

            spec = DeploymentSpec(
                name=name,
                namespace=namespace,
                sql_script=combined_sql,
                parallelism=1,
            )

            with VervericaClient("https://app.ververica.cloud", workspace_id, token) as client:
                status = client.create_sqlscript_deployment(spec)

            progress.update(task, completed=True)

        console.print(f"[green]✓[/green] Deployment created successfully!")
        console.print()
        console.print(f"[bold]Deployment Summary[/bold]")
        console.print(f"  • ID: {status.deployment_id}")
        console.print(f"  • Name: {status.name}")
        console.print(f"  • State: {status.state}")
        console.print(f"  • Namespace: {namespace}")
        console.print(f"  • Models: {len(processed_models)}")
        console.print()
        console.print(f"View in Ververica Cloud:")
        console.print(f"  https://app.ververica.cloud/workspaces/{workspace_id}/deployments/{status.deployment_id}")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]✗[/red] Workflow failed: {e}")
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
