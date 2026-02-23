from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workspace_cloud_provider import WorkspaceCloudProvider
from ..models.workspace_offering_type import WorkspaceOfferingType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.azure_credentials import AzureCredentials
    from ..models.cluster import Cluster
    from ..models.compute_units import ComputeUnits
    from ..models.workspace_status import WorkspaceStatus


T = TypeVar("T", bound="Workspace")


@_attrs_define
class Workspace:
    """A workspace is an isolated environment for deploying and managing applications,
    typically scoped to a specific user, team, or project. Workspaces are associated
    with a cloud region, a billing plan, and a compute cluster.

        Attributes:
            id (str | Unset): Unique identifier of the workspace. Example: q7760t0ym1d7xyso.
            creator_id (str | Unset): UUID of the user who created the workspace. Example:
                e967a977-6068-4355-99a9-bf387350b0dd.
            instance_id (str | Unset): Workspace instance ID. Example: q7760t0ym1d7xyso.
            name (str | Unset): Human-readable name of the workspace. Only letters, numbers, dashes (“-”), and underscores
                (“_”) are allowed. Example: workspace-name.
            status (WorkspaceStatus | Unset): Workspace status.
                When a workspace is being created, its status is in the PROCESSING category (name: "Creating").
                Once the workspace is ready and usable, the status changes to the OK category (name: "Running").
                Only when the category is OK can the user enter and interact with the workspace.
            user_role_id (str | Unset): Role of the current user in the workspace.
                Possible values:
                  - `admin`
                  - `owner`
                  - `editor`
                  - `viewer`
                 Example: owner.
            billing_plan_id (int | Unset): Identifier of the billing plan assigned to this workspace. Example: 10.
            offering_type (WorkspaceOfferingType | Unset): Type of offering associated with the workspace.
                - `PAYG`: Pay-as-you-go model.
                - `RC`: Reserved capacity model.
                - `BYOC`: Bring your own cloud infrastructure.
                 Example: PAYG.
            region_id (str | Unset): Identifier of the cloud region where the workspace is deployed. Example: aws-eu-west-1.
            compute_units (ComputeUnits | Unset): Number of Compute Units (CUs) to allocate for the workspace.
                Each Compute Unit corresponds to a fixed amount of physical resources, based on the following formula:

                **1 CU = 1 vCPU core + 4 GiB RAM**
                For example:
                  - `1.0` CU = 1 core, 4 GiB RAM
                  - `4.0` CU = 4 cores, 16 GiB RAM
            creation_time (str | Unset): ISO-8601 timestamp of when the workspace was created. Example: 2025-04-28
                13:02:15+00:00.
            deletion_time (str | Unset): ISO-8601 timestamp of when the workspace was deleted, or null if still active.
            console_uri (str | Unset): Direct link to the workspace view in the Ververica console. Example:
                https://app.dev.aws.ververica.cloud/console/#/workspaces/q7760t0ym1d7xyso/.
            cluster_id (UUID | Unset): UUID of the cluster the workspace is assigned to. Example:
                395cf992-1deb-4229-8991-71f0c7b1a06b.
            cluster (Cluster | Unset): Cluster details
            azure_credentials (AzureCredentials | Unset): Azure Credentials to setup private connection role
            cloud_provider (WorkspaceCloudProvider | Unset):
    """

    id: str | Unset = UNSET
    creator_id: str | Unset = UNSET
    instance_id: str | Unset = UNSET
    name: str | Unset = UNSET
    status: WorkspaceStatus | Unset = UNSET
    user_role_id: str | Unset = UNSET
    billing_plan_id: int | Unset = UNSET
    offering_type: WorkspaceOfferingType | Unset = UNSET
    region_id: str | Unset = UNSET
    compute_units: ComputeUnits | Unset = UNSET
    creation_time: str | Unset = UNSET
    deletion_time: str | Unset = UNSET
    console_uri: str | Unset = UNSET
    cluster_id: UUID | Unset = UNSET
    cluster: Cluster | Unset = UNSET
    azure_credentials: AzureCredentials | Unset = UNSET
    cloud_provider: WorkspaceCloudProvider | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        creator_id = self.creator_id

        instance_id = self.instance_id

        name = self.name

        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        user_role_id = self.user_role_id

        billing_plan_id = self.billing_plan_id

        offering_type: str | Unset = UNSET
        if not isinstance(self.offering_type, Unset):
            offering_type = self.offering_type.value

        region_id = self.region_id

        compute_units: dict[str, Any] | Unset = UNSET
        if not isinstance(self.compute_units, Unset):
            compute_units = self.compute_units.to_dict()

        creation_time = self.creation_time

        deletion_time = self.deletion_time

        console_uri = self.console_uri

        cluster_id: str | Unset = UNSET
        if not isinstance(self.cluster_id, Unset):
            cluster_id = str(self.cluster_id)

        cluster: dict[str, Any] | Unset = UNSET
        if not isinstance(self.cluster, Unset):
            cluster = self.cluster.to_dict()

        azure_credentials: dict[str, Any] | Unset = UNSET
        if not isinstance(self.azure_credentials, Unset):
            azure_credentials = self.azure_credentials.to_dict()

        cloud_provider: str | Unset = UNSET
        if not isinstance(self.cloud_provider, Unset):
            cloud_provider = self.cloud_provider.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if creator_id is not UNSET:
            field_dict["creatorId"] = creator_id
        if instance_id is not UNSET:
            field_dict["instanceId"] = instance_id
        if name is not UNSET:
            field_dict["name"] = name
        if status is not UNSET:
            field_dict["status"] = status
        if user_role_id is not UNSET:
            field_dict["userRoleId"] = user_role_id
        if billing_plan_id is not UNSET:
            field_dict["billingPlanId"] = billing_plan_id
        if offering_type is not UNSET:
            field_dict["offeringType"] = offering_type
        if region_id is not UNSET:
            field_dict["regionId"] = region_id
        if compute_units is not UNSET:
            field_dict["computeUnits"] = compute_units
        if creation_time is not UNSET:
            field_dict["creationTime"] = creation_time
        if deletion_time is not UNSET:
            field_dict["deletionTime"] = deletion_time
        if console_uri is not UNSET:
            field_dict["consoleUri"] = console_uri
        if cluster_id is not UNSET:
            field_dict["clusterId"] = cluster_id
        if cluster is not UNSET:
            field_dict["cluster"] = cluster
        if azure_credentials is not UNSET:
            field_dict["azureCredentials"] = azure_credentials
        if cloud_provider is not UNSET:
            field_dict["cloudProvider"] = cloud_provider

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.azure_credentials import AzureCredentials
        from ..models.cluster import Cluster
        from ..models.compute_units import ComputeUnits
        from ..models.workspace_status import WorkspaceStatus

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        creator_id = d.pop("creatorId", UNSET)

        instance_id = d.pop("instanceId", UNSET)

        name = d.pop("name", UNSET)

        _status = d.pop("status", UNSET)
        status: WorkspaceStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = WorkspaceStatus.from_dict(_status)

        user_role_id = d.pop("userRoleId", UNSET)

        billing_plan_id = d.pop("billingPlanId", UNSET)

        _offering_type = d.pop("offeringType", UNSET)
        offering_type: WorkspaceOfferingType | Unset
        if isinstance(_offering_type, Unset):
            offering_type = UNSET
        else:
            offering_type = WorkspaceOfferingType(_offering_type)

        region_id = d.pop("regionId", UNSET)

        _compute_units = d.pop("computeUnits", UNSET)
        compute_units: ComputeUnits | Unset
        if isinstance(_compute_units, Unset):
            compute_units = UNSET
        else:
            compute_units = ComputeUnits.from_dict(_compute_units)

        creation_time = d.pop("creationTime", UNSET)

        deletion_time = d.pop("deletionTime", UNSET)

        console_uri = d.pop("consoleUri", UNSET)

        _cluster_id = d.pop("clusterId", UNSET)
        cluster_id: UUID | Unset
        if isinstance(_cluster_id, Unset):
            cluster_id = UNSET
        else:
            cluster_id = UUID(_cluster_id)

        _cluster = d.pop("cluster", UNSET)
        cluster: Cluster | Unset
        if isinstance(_cluster, Unset):
            cluster = UNSET
        else:
            cluster = Cluster.from_dict(_cluster)

        _azure_credentials = d.pop("azureCredentials", UNSET)
        azure_credentials: AzureCredentials | Unset
        if isinstance(_azure_credentials, Unset):
            azure_credentials = UNSET
        else:
            azure_credentials = AzureCredentials.from_dict(_azure_credentials)

        _cloud_provider = d.pop("cloudProvider", UNSET)
        cloud_provider: WorkspaceCloudProvider | Unset
        if isinstance(_cloud_provider, Unset):
            cloud_provider = UNSET
        else:
            cloud_provider = WorkspaceCloudProvider(_cloud_provider)

        workspace = cls(
            id=id,
            creator_id=creator_id,
            instance_id=instance_id,
            name=name,
            status=status,
            user_role_id=user_role_id,
            billing_plan_id=billing_plan_id,
            offering_type=offering_type,
            region_id=region_id,
            compute_units=compute_units,
            creation_time=creation_time,
            deletion_time=deletion_time,
            console_uri=console_uri,
            cluster_id=cluster_id,
            cluster=cluster,
            azure_credentials=azure_credentials,
            cloud_provider=cloud_provider,
        )

        workspace.additional_properties = d
        return workspace

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
