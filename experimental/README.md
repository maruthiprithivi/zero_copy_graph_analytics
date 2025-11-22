# Experimental Code

This directory contains experimental features and alternative implementations that are not currently integrated into the main application workflow.

## Purpose

Code in this directory is:
- Experimental or proof-of-concept implementations
- Alternative approaches being evaluated
- Features being developed but not yet production-ready
- Code kept for potential future use or reference

## Current Files

### persona_generator.py

**Status**: Not integrated

**Purpose**: Enhanced persona-based data generator for massive scale (10M+ customers, 1B+ transactions)

**Features**:
- Generates 5 main personas with connected networks
- Creates rich relationship networks between customers
- Supports massive scale scenarios beyond the standard generator
- Alternative implementation to `app/data/generator.py`

**Why Not Used**:
- The main `app/data/generator.py` is sufficient for current demo use cases (1M-10M customers)
- This implementation adds complexity that's not needed for typical demonstrations
- Kept for potential future large-scale testing or if persona-based generation is needed

**How to Use** (if needed):
```bash
# This generator is standalone and can be run independently
# It's not integrated with generate_data.py CLI
python experimental/persona_generator.py
```

## Guidelines for Experimental Code

1. **Documentation**: Each experimental file should be documented here
2. **Status**: Mark clearly whether code is abandoned, in-development, or on-hold
3. **Integration Path**: Note what would be needed to integrate into main codebase
4. **Cleanup**: Periodically review and remove code that's no longer relevant

## Integration Process

To move code from experimental to production:
1. Ensure it passes all quality standards
2. Add appropriate tests
3. Update main documentation
4. Integrate with CLI tools (`generate_data.py`)
5. Remove from experimental directory
6. Update this README
