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

**First contact with a local LLM (14 Oct 2026):** a local Qwen, through Hermes Agent, operated the Director in a first test and a real conversation. It built a room from one sentence correctly, but also made errors (ignored parts of a request, invented a size, changed the scene after being criticized). What happened and what changed is in [`hermes/README.md`](hermes/README.md). Not measured yet.

**Changes on 14 Oct 2026** (after the first contact with the local LLM):
- **Rooms of any size** (fixes [#1](https://github.com/talisp/Director/issues/1)): the 2–20 m limit was removed; a room only needs sizes above zero (a 1 × 3 m corridor and a 0.6 × 0.5 m closet were built in Unreal).
- **Rooms side by side share one wall** (fixes [#2](https://github.com/talisp/Director/issues/2)): placed 0.15 m apart (one wall), two rooms get a single 15 cm wall instead of two, and a door in it is the passage from one room to the other. A door or window that would open against another wall is refused. Tested without Unreal (53 tests; existing scenes unchanged); **not yet built in Unreal**.
- **Approval card in Hermes** (fixes [#3](https://github.com/talisp/Director/issues/3)): a Hermes plugin (`hermes/plugins/director-guarda/`) stops every command that could change Unreal and shows the person what the ficha will do; it only runs if the person approves. The LLM can only write files in `work/fichas/` and `work/propostas/`.
- **Questions reach the person** (fixes [#5](https://github.com/talisp/Director/issues/5)): the same plugin repairs the question list when the model sends it as text (with a stray `}` or a missing `]`); the 15 questions recorded in real conversations pass Hermes' own validation.
- Operator rules: planning is not doing; a question or criticism is not an order; authorization is the approval card, never loose text.

**Not there yet:** a measured LLM filling the fichas reliably; characters with a body and animation; real-looking parts (everything is cubes and cylinders); Smart Objects; sequences, camera and video; an opening without a door between rooms.

> The numbers above are from the run of 13 Oct 2026, 20:10, made before the package was renamed from `director2` to `director`. After the rename the whole run was repeated on a new scene (22:52): 64 of 64 again, and 33 of 33 tests without Unreal (53 since the changes of 14 Oct).

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
| [`hermes/`](hermes/README.md) | instructions for a local LLM operating the Director through Hermes Agent (rules, skill, profile installer), and what the first test showed |
| [`docs/CONHECIMENTO.md`](docs/CONHECIMENTO.md) | what is reusable, which Epic APIs are used, pitfalls already measured, what is verified, provisional or only a hypothesis, and how to resume |

Code comments and documents are in Portuguese.

## License

Source-available, not open source. See [LICENSE](LICENSE).
