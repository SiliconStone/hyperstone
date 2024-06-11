"""
Demo for ELF files.
"""
import hyperstone
import megastone

base_address = 0  # TODO: randomize

SETTINGS = [

    # TODO: add loader here

    hyperstone.plugins.memory.InitializeSupportStack(),

    hyperstone.plugins.memory.EnforceMemory(),

    hyperstone.plugins.runners.FunctionEntrypoint(base_address)
]


def main():
    hyperstone.start(megastone.ARCH_ARM, SETTINGS)


if __name__ == '__main__':
    main()

