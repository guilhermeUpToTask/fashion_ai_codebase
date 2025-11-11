import pytest
from src.domain.image_analysis.errors import InvalidBoundingBox
from src.domain.image_analysis.value_objects.clothing_item_value_objects import (
    Label,
    BoundingBox,
    ClothingItemId,
)
from src.domain.shared.value_objects import DescriptiveString


# ID
def test_clothing_id_is_correct_instance():
    id = ClothingItemId.next_id()
    assert isinstance(id, ClothingItemId)


# Label
def test_label_str_representation():
    label = Label(
        category=DescriptiveString("shirt"),
        color=DescriptiveString("red"),
        pattern=DescriptiveString("striped"),
        style=DescriptiveString("casual"),
    )
    assert str(label) == "casual red striped shirt"


# BoundingBox
def test_valid_bounding_box():
    bbox = BoundingBox(x_min=10, x_max=50, y_min=20, y_max=80)
    assert bbox.width == 40
    assert bbox.height == 60
    assert bbox.area == 2400
    assert bbox.as_tuple() == (10, 20, 50, 80)
    assert bbox.as_dict() == {"x_min": 10, "y_min": 20, "x_max": 50, "y_max": 80}


@pytest.mark.parametrize(
    "x_min, x_max, y_min, y_max",
    [
        (-1, 50, 10, 80),
        (10, -50, 10, 80),
        (10, 50, -10, 80),
        (10, 50, 10, -80),
    ],
)
def test_invalid_negative_coordinates(x_min, x_max, y_min, y_max):
    with pytest.raises(InvalidBoundingBox, match="non-negative"):
        BoundingBox(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)


@pytest.mark.parametrize(
    "x_min, x_max, y_min, y_max",
    [
        (10, 10, 10, 80),
        (10, 5, 10, 80),
        (10, 50, 10, 10),
        (10, 50, 20, 10),
    ],
)
def test_invalid_min_max_order(x_min, x_max, y_min, y_max):
    with pytest.raises(InvalidBoundingBox, match="greater than min"):
        BoundingBox(x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)


def test_bounding_box_equality_and_hash():
    b1 = BoundingBox(x_min=0, x_max=10, y_min=0, y_max=20)
    b2 = BoundingBox(x_min=0, x_max=10, y_min=0, y_max=20)
    assert b1 == b2
    assert hash(b1) == hash(b2)
