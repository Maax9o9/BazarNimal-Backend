from src.features.adoptions.admin.data.dtos.adoption_admin_dtos import AdoptionRequestAdminDto
from src.features.adoptions.admin.data.mappers.adoption_admin_mapper import adoption_request_to_dto
from src.features.adoptions.admin.domain.usecases.approve_adoption_request_usecase import (
    ApproveAdoptionRequestUseCase,
)
from src.features.adoptions.admin.domain.usecases.get_adoption_request_by_id_usecase import (
    GetAdoptionRequestByIdUseCase,
)
from src.features.adoptions.admin.domain.usecases.get_adoption_requests_usecase import GetAdoptionRequestsUseCase
from src.features.adoptions.admin.domain.usecases.reject_adoption_request_usecase import (
    RejectAdoptionRequestUseCase,
)
from src.features.adoptions.admin.infrastructure.validators.adoption_admin_validators import AdoptionRequestListQuery
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import PaginatedResponse, SuccessResponse, ok, paginated


class AdoptionRequestAdminController:
    def __init__(
        self,
        get_requests: GetAdoptionRequestsUseCase,
        get_request_by_id: GetAdoptionRequestByIdUseCase,
        approve_request: ApproveAdoptionRequestUseCase,
        reject_request: RejectAdoptionRequestUseCase,
    ) -> None:
        self._get_requests = get_requests
        self._get_request_by_id = get_request_by_id
        self._approve_request = approve_request
        self._reject_request = reject_request

    async def list(self, query: AdoptionRequestListQuery) -> PaginatedResponse[AdoptionRequestAdminDto]:
        page = await self._get_requests.execute(query.to_filters(), query.to_page_request())
        return paginated([adoption_request_to_dto(item) for item in page.items], page)

    async def get(self, request_id: str) -> SuccessResponse[AdoptionRequestAdminDto]:
        return ok(adoption_request_to_dto(await self._get_request_by_id.execute(request_id)))

    async def approve(self, request_id: str, admin: CurrentUser) -> SuccessResponse[AdoptionRequestAdminDto]:
        request = await self._approve_request.execute(request_id, admin.id)
        return ok(adoption_request_to_dto(request), "Solicitud aprobada. La mascota quedó como adoptada.")

    async def reject(self, request_id: str, admin: CurrentUser) -> SuccessResponse[AdoptionRequestAdminDto]:
        request = await self._reject_request.execute(request_id, admin.id)
        return ok(adoption_request_to_dto(request), "Solicitud rechazada")
