"""
A module for defining naming conventions
"""


# Following the name convention from PE.

SEGMENT_NAME = "{fmt}.SEGMENT.{file_name}.{segment_name}"

PE_SEGMENT_NAME = SEGMENT_NAME.format(fmt="PE")
ELF_SEGMENT_NAME = SEGMENT_NAME.format(fmt="ELF")

