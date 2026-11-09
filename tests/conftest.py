"""Import the protocol module without loading Home Assistant."""
from pathlib import Path
import sys
import types

root = Path(__file__).parents[1] / "custom_components" / "vguard_inverter"
package = types.ModuleType("vguard")
package.__path__ = [str(root)]
sys.modules["vguard"] = package
