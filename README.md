# Director

**Builds and edits functional 3D scenes in Unreal Engine from small structured requests, so that a small or local LLM only has to fill in parameters.**

The LLM (or a person) writes a *ficha*: a short JSON with an operation and a few fields ("create a 4 × 4 m room", "move the door to the opposite wall"). A deterministic core, with no LLM inside, validates it, plans the smallest change, asks Unreal to do it with Unreal's own automation, measures the result and saves. If anything fails, the scene goes back to what it was.

> **Director is the successor of [unreal-local-director](https://github.com/talisp/unreal-local-director), now called "Antigo Director" (Old Director), which is discontinued.** An explanation of why will come later.

## Status: early, first delivery only

Measured on 13 Oct 2026, Unreal Engine 5.8.3, in a separate lab project ([numbers](docs/entrega1/README.md)):

| Request | What happened in Unreal |
|---|---|
| "Create a 4 × 4 m room with a door, a window and a table." | 9 parts created; inner size measured by ray: 400.0 × 400.0 cm |
| "Make the room 5 × 4 m and move the door to the opposite wall." | 7 parts updated, none deleted or recreated; a table moved by hand stayed where the person left it |
| "Put a plate and a glass on the table." | 2 physical objects; with physics running they stayed on the table |

Also measured: the door blocks when closed and frees the way when open; an Unreal `Character` walks in through the open door; save, close the editor and reopen keeps everything; what moved during Play can be written back to the saved scene; an invalid request is refused before touching the scene; a failure in the middle is rolled back. 64 of 64 checks in the final run, 33 of 33 tests without Unreal.

**Not there yet:** an LLM actually filling the fichas (the three above were written by hand); characters with a body and animation; real-looking parts (everything is cubes and cylinders); Smart Objects; sequences, camera and video; more than one room.

> The numbers above are from the run of 13 Oct 2026, 20:10, made before the package was renamed from `director2` to `director`. After the rename the whole run was repeated on a new scene (22:52): 64 of 64 again, and 33 of 33 tests without Unreal.

## Try it

Needs Python 3.11+ (standard library only). Without Unreal:

```
python -m unittest director.testes.testes_nucleo
python -m director capacidades
```

With Unreal Engine 5.8 installed (creates and opens a small lab project; it never talks to another project):

```
python -m director.lab criar
python -m director.lab abrir
python -m director pecas
python -m director fazer sala director/fichas/comando1.json
```

## Where things are

| Path | What |
|---|---|
| `director/nucleo/` | the core: operations and refusals, the scene plan (*planta*), minimal-change planner, executor with rollback |
| `director/nucleo/pecas.py` | the parts: each one is a Blueprint with a Construction Script, created by the program |
| `director/editor/` | what runs inside the Unreal editor |
| `director/ponte.py`, `director/lab.py` | protections and the lab project |
| `director/fichas/` | the three example requests |
| [`docs/CONHECIMENTO.md`](docs/CONHECIMENTO.md) | what is reusable, which Epic APIs are used, pitfalls already measured, what is verified, provisional or only a hypothesis, and how to resume |

Code comments and documents are in Portuguese.

## License

Source-available, not open source. See [LICENSE](LICENSE).
