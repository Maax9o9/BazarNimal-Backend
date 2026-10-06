import pytest

from src.core.errors.exceptions import ConflictError, NotFoundError
from src.features.adoptions.admin.domain.entities.adoption_request import (
    AdoptionRequest,
    AdoptionRequestStatus,
    Applicant,
)
from src.features.adoptions.admin.domain.entities.pet import PetStatus
from src.features.adoptions.admin.domain.usecases.approve_adoption_request_usecase import (
    ApproveAdoptionRequestUseCase,
)
from src.features.adoptions.admin.domain.usecases.reject_adoption_request_usecase import (
    RejectAdoptionRequestUseCase,
)
from src.shared.utils.time import utcnow
from tests.unit.fakes import InMemoryAdoptionRequestRepository


def _request(request_id: str, status=AdoptionRequestStatus.PENDING, pet_status=PetStatus.IN_ADOPTION):
    return AdoptionRequest(
        id=request_id,
        status=status,
        pet_id="pet-1",
        pet_name="Firulais",
        pet_status=pet_status,
        applicant=Applicant(id=f"user-{request_id}", name="Ana", email="ana@example.com", phone="5512345678"),
        reviewed_at=None,
        created_at=utcnow(),
    )


async def test_approve_marks_pet_adopted_and_rejects_others():
    repo = InMemoryAdoptionRequestRepository([_request("a"), _request("b")])
    approved = await ApproveAdoptionRequestUseCase(repo).execute("a", "admin-1")
    assert approved.status is AdoptionRequestStatus.APPROVED
    assert approved.pet_status is PetStatus.ADOPTED
    assert repo.requests["b"].status is AdoptionRequestStatus.REJECTED


async def test_cannot_approve_reviewed_request_or_adopted_pet():
    repo = InMemoryAdoptionRequestRepository(
        [_request("a", status=AdoptionRequestStatus.REJECTED), _request("b", pet_status=PetStatus.ADOPTED)]
    )
    usecase = ApproveAdoptionRequestUseCase(repo)
    with pytest.raises(ConflictError):
        await usecase.execute("a", "admin-1")
    with pytest.raises(ConflictError):
        await usecase.execute("b", "admin-1")
    assert repo.approved == []


async def test_missing_request_is_not_found():
    repo = InMemoryAdoptionRequestRepository([])
    with pytest.raises(NotFoundError):
        await RejectAdoptionRequestUseCase(repo).execute("nope", "admin-1")
