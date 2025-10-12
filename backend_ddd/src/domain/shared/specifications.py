from abc import ABC, abstractmethod
from typing import Any


class Specification(ABC):
    @abstractmethod
    def accept(self, visitor: "SpecificationVisitor") -> Any:
        pass

    def and_(self, other: "Specification") -> "AndSpecification":
        return AndSpecification(self, other)

    def or_(self, other: "Specification") -> "OrSpecification":
        return OrSpecification(self, other)


class FieldSpecification(Specification):
    def __init__(self, field_name: str, op: str, value: Any):
        self.field_name = field_name
        self.op = op
        self.value = value

    def accept(self, visitor: "SpecificationVisitor") -> Any:
        return visitor.visit_field(self)


class AndSpecification(Specification):
    def __init__(self, *specifications: Specification):
        self.specifications = specifications

    def accept(self, visitor: "SpecificationVisitor") -> Any:
        return visitor.visit_and(self)


class OrSpecification(Specification):
    def __init__(self, *specifications: Specification):
        self.specifications = specifications

    def accept(self, visitor: "SpecificationVisitor") -> Any:
        return visitor.visit_or(self)


class SpecificationVisitor(ABC):
    @abstractmethod
    def visit_field(self, spec: FieldSpecification) -> Any:
        pass

    @abstractmethod
    def visit_and(self, spec: AndSpecification) -> Any:
        pass

    @abstractmethod
    def visit_or(self, spec: OrSpecification) -> Any:
        pass
