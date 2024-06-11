# Emulation source

What do we need in order to start an emulation?
1. stack
2. entry point
3. instructions

## Instruction sources
1. Pure assembly
2. Bytes
3. Executable format

### Pure assembly

```python
import hyperstone as hs
hs.plugins.memory.CodeStream(assembly="...")
```

### Bytes
```python
import hyperstone as hs

hs.plugins.memory.RawStream(data=b"...")
```