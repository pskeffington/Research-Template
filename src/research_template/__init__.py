"""Independent, reusable research workflow utilities.

Author: Paul Skeffington. Prepared with OpenAI.
"""

from .quality import DataContractError, validate_cohort
from .synthetic import make_cohort

__all__ = ["DataContractError", "make_cohort", "validate_cohort"]
__version__ = "0.1.0"
