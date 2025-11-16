from typing import Any
from sqlmodel import or_, and_
from src.domain.shared.specifications import AndSpecification, OrSpecification, SpecificationVisitor, FieldSpecification


class SQLModelSpecificationVisitor(SpecificationVisitor):
    def __init__(self, field_map: dict[str, Any]):
        self.field_map = field_map
    
    def visit_field(self, spec: FieldSpecification) -> Any:
        column = self.field_map.get(spec.field_name)
        if not column:
            raise ValueError(f"Unknown field: {spec.field_name}")

        if spec.op == "eq":
            return column == spec.value
        if spec.op == "gt":
            return column > spec.value
        if spec.op == "lt":
            return column < spec.value
        #More operators can be added here as its needs (like, betwen, etc)
        raise ValueError(f"Unknown operator:{spec.op}")

    def visit_and(self, spec: AndSpecification) -> Any:
        conditions = [s.accept(self) for s in spec.specifications]
        return and_(*conditions)

    def visit_or(self, spec: OrSpecification) -> Any:
        conditions = [s.accept(self) for s in spec.specifications]
        return or_(*conditions)