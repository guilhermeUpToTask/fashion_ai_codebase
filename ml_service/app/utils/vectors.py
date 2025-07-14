import torch
import torch.nn.functional as F
def merge_two_vectors(vector1: torch.Tensor, vector2: torch.Tensor) -> torch.Tensor:

    # Average and normalize again
    merged = (vector1 + vector2) / 2
    merged = F.normalize(merged, p=2, dim=-1)
    return merged