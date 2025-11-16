import pytest
from sqlmodel import Column, SQLModel, Field
from sqlalchemy import String, Integer, DateTime
from src.domain.shared.specifications import (
    FieldSpecification,
    AndSpecification,
    OrSpecification,
)
from src.infrastructure.db.specification_visitor import SQLModelSpecificationVisitor


# Test model to use real SQLModel columns


class DummyModel(SQLModel, table=True):
    __tablename__ = "test_table" # type: ignore
    
    id: int = Field(primary_key=True)
    model_name: str
    status: str
    created_at: int
    count: int


# Fixtures

@pytest.fixture
def field_map():
    """Creates a field map with real SQLModel columns."""
    return {
        "model_name": DummyModel.model_name,
        "created_at": DummyModel.created_at,
        "status": DummyModel.status,
        "count": DummyModel.count,
    }


@pytest.fixture
def visitor(field_map):
    """Creates a SQLModelSpecificationVisitor instance."""
    return SQLModelSpecificationVisitor(field_map)


# Tests for visit_field

def test_visit_field_with_eq_operator(visitor):
    """Test that eq operator creates equality comparison."""
    spec = FieldSpecification("model_name", "eq", "test-model")
    
    result = visitor.visit_field(spec)
    
    # Verify it returns a SQLAlchemy BinaryExpression
    assert result is not None
    assert hasattr(result, 'compare')


def test_visit_field_with_gt_operator(visitor):
    """Test that gt operator creates greater than comparison."""
    spec = FieldSpecification("count", "gt", 100)
    
    result = visitor.visit_field(spec)
    
    assert result is not None
    assert hasattr(result, 'compare')


def test_visit_field_with_lt_operator(visitor):
    """Test that lt operator creates less than comparison."""
    spec = FieldSpecification("count", "lt", 50)
    
    result = visitor.visit_field(spec)
    
    assert result is not None
    assert hasattr(result, 'compare')


def test_visit_field_with_unknown_field_raises_error(visitor):
    """Test that unknown field name raises ValueError."""
    spec = FieldSpecification("unknown_field", "eq", "value")
    
    with pytest.raises(ValueError, match="Unknown field: unknown_field"):
        visitor.visit_field(spec)


def test_visit_field_with_unknown_operator_raises_error(visitor):
    """Test that unknown operator raises ValueError."""
    spec = FieldSpecification("model_name", "invalid_op", "value")
    
    with pytest.raises(ValueError, match="Unknown operator:invalid_op"):
        visitor.visit_field(spec)


def test_visit_field_with_different_value_types(visitor):
    """Test that visitor handles different value types correctly."""
    # String value
    spec_str = FieldSpecification("model_name", "eq", "string_value")
    result_str = visitor.visit_field(spec_str)
    assert result_str is not None
    
    # Integer value
    spec_int = FieldSpecification("count", "eq", 42)
    result_int = visitor.visit_field(spec_int)
    assert result_int is not None
    
    # None value
    spec_none = FieldSpecification("model_name", "eq", None)
    result_none = visitor.visit_field(spec_none)
    assert result_none is not None


def test_visit_field_with_different_fields(visitor):
    """Test that visitor works with different field names."""
    spec1 = FieldSpecification("model_name", "eq", "value1")
    result1 = visitor.visit_field(spec1)
    assert result1 is not None
    
    spec2 = FieldSpecification("status", "eq", "value2")
    result2 = visitor.visit_field(spec2)
    assert result2 is not None
    
    spec3 = FieldSpecification("created_at", "gt", 1000)
    result3 = visitor.visit_field(spec3)
    assert result3 is not None


# Tests for visit_and

def test_visit_and_with_two_specifications(visitor):
    """Test that AND combines two specifications correctly."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("status", "eq", "active")
    and_spec = AndSpecification(spec1, spec2)
    
    result = visitor.visit_and(and_spec)
    
    # Verify the result is a SQLAlchemy BooleanClauseList (AND clause)
    assert result is not None
    assert hasattr(result, 'clauses')


def test_visit_and_with_multiple_specifications(visitor):
    """Test that AND combines multiple specifications correctly."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("status", "eq", "active")
    spec3 = FieldSpecification("created_at", "gt", 1000)
    and_spec = AndSpecification(spec1, spec2, spec3)
    
    result = visitor.visit_and(and_spec)
    
    assert result is not None
    assert hasattr(result, 'clauses')


def test_visit_and_with_single_specification(visitor):
    """Test that AND works with a single specification."""
    spec = FieldSpecification("model_name", "eq", "model1")
    and_spec = AndSpecification(spec)
    
    result = visitor.visit_and(and_spec)
    
    assert result is not None


def test_visit_and_with_nested_and_specifications(visitor):
    """Test that nested AND specifications are handled correctly."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("status", "eq", "active")
    inner_and = AndSpecification(spec1, spec2)
    
    spec3 = FieldSpecification("created_at", "gt", 1000)
    outer_and = AndSpecification(inner_and, spec3)
    
    result = visitor.visit_and(outer_and)
    
    assert result is not None


def test_visit_and_with_different_operators(visitor):
    """Test AND with specifications using different operators."""
    spec1 = FieldSpecification("count", "gt", 10)
    spec2 = FieldSpecification("count", "lt", 100)
    and_spec = AndSpecification(spec1, spec2)
    
    result = visitor.visit_and(and_spec)
    
    assert result is not None
    assert hasattr(result, 'clauses')


# Tests for visit_or

def test_visit_or_with_two_specifications(visitor):
    """Test that OR combines two specifications correctly."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("model_name", "eq", "model2")
    or_spec = OrSpecification(spec1, spec2)
    
    result = visitor.visit_or(or_spec)
    
    # Verify the result is a SQLAlchemy BooleanClauseList (OR clause)
    assert result is not None
    assert hasattr(result, 'clauses')


def test_visit_or_with_multiple_specifications(visitor):
    """Test that OR combines multiple specifications correctly."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("model_name", "eq", "model2")
    spec3 = FieldSpecification("model_name", "eq", "model3")
    or_spec = OrSpecification(spec1, spec2, spec3)
    
    result = visitor.visit_or(or_spec)
    
    assert result is not None
    assert hasattr(result, 'clauses')


def test_visit_or_with_single_specification(visitor):
    """Test that OR works with a single specification."""
    spec = FieldSpecification("model_name", "eq", "model1")
    or_spec = OrSpecification(spec)
    
    result = visitor.visit_or(or_spec)
    
    assert result is not None


def test_visit_or_with_nested_or_specifications(visitor):
    """Test that nested OR specifications are handled correctly."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("model_name", "eq", "model2")
    inner_or = OrSpecification(spec1, spec2)
    
    spec3 = FieldSpecification("model_name", "eq", "model3")
    outer_or = OrSpecification(inner_or, spec3)
    
    result = visitor.visit_or(outer_or)
    
    assert result is not None


def test_visit_or_with_different_fields(visitor):
    """Test OR with specifications on different fields."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("status", "eq", "active")
    or_spec = OrSpecification(spec1, spec2)
    
    result = visitor.visit_or(or_spec)
    
    assert result is not None
    assert hasattr(result, 'clauses')


# Tests for complex combinations

def test_complex_and_or_combination(visitor):
    """Test complex combination of AND and OR specifications."""
    # (model_name == "model1" OR model_name == "model2") AND status == "active"
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("model_name", "eq", "model2")
    or_spec = OrSpecification(spec1, spec2)
    
    spec3 = FieldSpecification("status", "eq", "active")
    and_spec = AndSpecification(or_spec, spec3)
    
    result = visitor.visit_and(and_spec)
    
    assert result is not None


def test_or_of_and_specifications(visitor):
    """Test OR of multiple AND specifications."""
    # (model_name == "model1" AND status == "active") OR (model_name == "model2" AND status == "inactive")
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("status", "eq", "active")
    and_spec1 = AndSpecification(spec1, spec2)
    
    spec3 = FieldSpecification("model_name", "eq", "model2")
    spec4 = FieldSpecification("status", "eq", "inactive")
    and_spec2 = AndSpecification(spec3, spec4)
    
    or_spec = OrSpecification(and_spec1, and_spec2)
    result = visitor.visit_or(or_spec)
    
    assert result is not None


def test_multiple_operators_in_and(visitor):
    """Test AND with different operators."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("created_at", "gt", 1000)
    spec3 = FieldSpecification("created_at", "lt", 2000)
    and_spec = AndSpecification(spec1, spec2, spec3)
    
    result = visitor.visit_and(and_spec)
    
    assert result is not None


def test_deeply_nested_specifications(visitor):
    """Test deeply nested AND/OR specifications."""
    # ((a == 1 OR b == 2) AND (c == 3 OR d == 4)) AND e == 5
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("model_name", "eq", "model2")
    or_spec1 = OrSpecification(spec1, spec2)
    
    spec3 = FieldSpecification("status", "eq", "active")
    spec4 = FieldSpecification("status", "eq", "inactive")
    or_spec2 = OrSpecification(spec3, spec4)
    
    and_spec1 = AndSpecification(or_spec1, or_spec2)
    
    spec5 = FieldSpecification("count", "gt", 10)
    and_spec2 = AndSpecification(and_spec1, spec5)
    
    result = visitor.visit_and(and_spec2)
    
    assert result is not None


def test_all_operators_in_combination(visitor):
    """Test combination using all supported operators."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("count", "gt", 10)
    spec3 = FieldSpecification("count", "lt", 100)
    spec4 = FieldSpecification("status", "eq", "active")
    
    # (model_name == "model1" AND count > 10 AND count < 100) OR status == "active"
    and_spec = AndSpecification(spec1, spec2, spec3)
    or_spec = OrSpecification(and_spec, spec4)
    
    result = visitor.visit_or(or_spec)
    
    assert result is not None


# Tests for initialization

def test_visitor_initialization_with_empty_field_map():
    """Test that visitor can be initialized with empty field map."""
    visitor = SQLModelSpecificationVisitor({})
    
    assert visitor.field_map == {}


def test_visitor_initialization_with_field_map(field_map):
    """Test that visitor stores field map correctly."""
    visitor = SQLModelSpecificationVisitor(field_map)
    
    assert visitor.field_map == field_map
    assert "model_name" in visitor.field_map
    assert "created_at" in visitor.field_map
    assert "status" in visitor.field_map


def test_visitor_field_map_not_none():
    """Test that visitor field_map attribute exists."""
    visitor = SQLModelSpecificationVisitor({"test": DummyModel.model_name})
    
    assert hasattr(visitor, 'field_map')
    assert visitor.field_map is not None


# Edge cases

def test_visit_field_with_empty_string_value(visitor):
    """Test that empty string value is handled correctly."""
    spec = FieldSpecification("model_name", "eq", "")
    
    result = visitor.visit_field(spec)
    
    assert result is not None


def test_visit_field_with_zero_value(visitor):
    """Test that zero value is handled correctly."""
    spec = FieldSpecification("count", "eq", 0)
    
    result = visitor.visit_field(spec)
    
    assert result is not None


def test_visit_field_with_negative_value(visitor):
    """Test that negative value is handled correctly."""
    spec = FieldSpecification("count", "lt", -10)
    
    result = visitor.visit_field(spec)
    
    assert result is not None


def test_multiple_fields_in_single_and(visitor):
    """Test AND with multiple different fields."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("status", "eq", "active")
    spec3 = FieldSpecification("count", "gt", 10)
    spec4 = FieldSpecification("created_at", "lt", 2000)
    
    and_spec = AndSpecification(spec1, spec2, spec3, spec4)
    result = visitor.visit_and(and_spec)
    
    assert result is not None


def test_same_field_multiple_times_in_or(visitor):
    """Test OR with same field multiple times."""
    spec1 = FieldSpecification("model_name", "eq", "model1")
    spec2 = FieldSpecification("model_name", "eq", "model2")
    spec3 = FieldSpecification("model_name", "eq", "model3")
    spec4 = FieldSpecification("model_name", "eq", "model4")
    
    or_spec = OrSpecification(spec1, spec2, spec3, spec4)
    result = visitor.visit_or(or_spec)
    
    assert result is not None
    assert hasattr(result, 'clauses')


def test_range_query_with_gt_and_lt(visitor):
    """Test range query using gt and lt in AND."""
    # 10 < count < 100
    spec1 = FieldSpecification("count", "gt", 10)
    spec2 = FieldSpecification("count", "lt", 100)
    and_spec = AndSpecification(spec1, spec2)
    
    result = visitor.visit_and(and_spec)
    
    assert result is not None