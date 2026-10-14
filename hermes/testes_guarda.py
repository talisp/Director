"""Testes do complemento director-guarda (sem Hermes e sem Unreal).

Na raiz do Director:  python -m unittest hermes.testes_guarda
"""
import importlib.util
import json
import os
import tempfile
import unittest

_AQUI = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("director_guarda", os.path.join(_AQUI, "plugins", "director-guarda", "__init__.py"))
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

PY = '"C:/x/venv/Scripts/python.exe"'


class Perguntas(unittest.TestCase):
    def test_lista_como_texto_vira_lista(self):
        # o erro que o Qwen repetiu três vezes em 14/10/2026
        texto = json.dumps([{"question": "Por onde começamos?", "choices": ["A", "B", "C"]}], ensure_ascii=False)
        novos = G.consertar_perguntas({"questions": texto})
        self.assertEqual(novos, {"questions": [{"question": "Por onde começamos?", "choices": ["A", "B", "C"]}]})

    def test_lista_como_texto_com_chave_sobrando(self):
        # o erro real do aplicativo (14/10/2026, 18:50 e 18:56): a lista como texto, com o "}" do objeto de fora no fim
        certas = [{"question": "Quantas portas ficam com 90 cm?", "choices": ["As duas", "Só a nova", "Nenhuma"]},
                  {"question": "Onde eu faço isso?", "choices": ["Ensaio", "Sala"]}]
        texto = json.dumps(certas, ensure_ascii=False) + "}"
        self.assertEqual(G.consertar_perguntas({"questions": texto}), {"questions": certas})
        # e do jeito que o Hermes deixa quando não consegue ler: o texto embrulhado numa lista
        self.assertEqual(G.consertar_perguntas({"questions": [texto]}), {"questions": certas})
        # a lista sem o "]" final (14/10/2026, cena ensaio)
        self.assertEqual(G.consertar_perguntas({"questions": json.dumps(certas[:1], ensure_ascii=False)[:-1]}),
                         {"questions": certas[:1]})
        # o objeto de fora inteiro como texto
        self.assertEqual(G.consertar_perguntas({"questions": json.dumps({"questions": certas})}), {"questions": certas})

    def test_opcoes_como_objetos_viram_texto(self):
        args = {"questions": [{"question": "Q?", "choices": [{"label": "Sim", "description": "x"}, {"label": "Não"}]}]}
        self.assertEqual(G.consertar_perguntas(args)["questions"][0]["choices"], ["Sim", "Não"])

    def test_pergunta_sozinha_vira_lista(self):
        self.assertEqual(G.consertar_perguntas({"questions": {"question": "Q?"}}), {"questions": [{"question": "Q?"}]})

    def test_formato_certo_nao_muda(self):
        self.assertIsNone(G.consertar_perguntas({"questions": [{"question": "Q?", "choices": ["Sim", "Não"]}]}))

    def test_lixo_nao_e_inventado(self):
        self.assertIsNone(G.consertar_perguntas({"questions": "isto não é json"}))
        self.assertIsNone(G.consertar_perguntas("nada"))


class Cartao(unittest.TestCase):
    def test_leituras_passam(self):
        for c in (f'cd "C:/x/Director" && {PY} -m director estado sala',
                  f'cd "C:/x/Director" && {PY} -m director capacidades',
                  f'cd "C:/x/Director" && {PY} -m director.lab estado',
                  f'{PY} -m director.lab estado && {PY} -m director estado sala',
                  'ls director/cenas', "cat work/fichas/a.json", "grep -n x director/nucleo/operacoes.py"):
            self.assertFalse(G.precisa_de_aprovacao(c), c)

    def test_o_que_muda_o_unreal_pede_cartao(self):
        for c in (f'cd "C:/x/Director" && {PY} -m director fazer sala work/fichas/a.json',
                  f'cd "C:/x/Director" && PYTHONUTF8=0 {PY} -m director fazer ensaio_casa work/fichas/a.json',
                  f'{PY} -m director incorporar sala', f'{PY} -m director pecas',
                  f'{PY} -m director.lab abrir', f'{PY} -m director.lab fechar',
                  # escapar das leituras: leitura junto com outra coisa, script próprio, rede
                  f'{PY} -m director estado sala && {PY} -m director fazer sala a.json',
                  f'{PY} meu_script.py', f'{PY} -c "import urllib"', "python teste.py", "py -3 x.py",
                  "curl http://127.0.0.1:8011/mcp", "Invoke-WebRequest http://localhost:8011"):
            self.assertTrue(G.precisa_de_aprovacao(c), c)

    def test_fichas_pelo_terminal_passam(self):
        for c in ('cd "C:/x/Director" && cat > work/fichas/a.json <<\'FIM\'\n{"operacoes": []}\nFIM',
                  "mkdir -p work/propostas/casa && ls work/propostas 2>/dev/null",
                  "grep -rn x director 2>&1 | head -20"):
            self.assertFalse(G.precisa_de_aprovacao(c), c)

    def test_desligar_a_trava_ou_mexer_no_codigo_pede_cartao(self):
        for c in ("cat > C:/Users/x/AppData/Local/hermes/profiles/director/config.yaml <<'FIM'\nx\nFIM",
                  "hermes -p director plugins disable director-guarda", "hermes config set approvals.mode off",
                  "echo x >> ~/.hermes/.env", "cat > director/nucleo/operacoes.py <<'FIM'\nx\nFIM",
                  "rm -rf director/cenas", "mv work/fichas/a.json director/", "sed -i s/a/b/ director/__main__.py",
                  "git commit -am x", 'echo x | tee director/x.py', '"C:/UE/UnrealEditor.exe" lab.uproject'):
            self.assertTrue(G.precisa_de_aprovacao(c), c)

    def test_escrever_arquivo_so_nas_pastas_certas(self):
        self.assertIsNone(G._antes_da_ferramenta("write_file", {"path": "C:/x/Director/work/fichas/a.json", "content": "{}"}))
        self.assertIsNone(G._antes_da_ferramenta("patch", {"path": "C:\\x\\Director\\work\\propostas\\p\\plano.md"}))
        for p in ("C:/x/Director/director/nucleo/operacoes.py", "C:/Users/x/AppData/Local/hermes/profiles/director/config.yaml",
                  "C:/x/Director/work/restauracao/sala/planta.json", "work/fichas_falsas/a.json", ""):
            r = G._antes_da_ferramenta("write_file", {"path": p, "content": "x"})
            self.assertEqual(r["action"], "block", p)

    def test_resumo_mostra_a_ficha(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "work", "fichas"))
            with open(os.path.join(d, "work", "fichas", "a.json"), "w", encoding="utf-8") as f:
                json.dump({"pedido": "Abra a porta e ponha uma janela.", "operacoes": [
                    {"operacao": "mudar", "id": "porta1", "angulo": 90},
                    {"operacao": "colocar", "tipo": "janela", "parede": "oeste", "largura_m": 1.2},
                    {"operacao": "criar_sala", "id": "corredor", "largura_m": 1, "comprimento_m": 3}]}, f)
            r = G.resumo_do_comando(f'cd "{d}" && {PY} -m director fazer sala work/fichas/a.json', d)
        self.assertIn("MUDAR a cena «sala»", r)
        self.assertIn("Pedido: Abra a porta e ponha uma janela.", r)
        self.assertIn("mudar «porta1» (abertura 90°)", r)
        self.assertIn("colocar janela (parede oeste, largura 1.2 m)", r)
        self.assertIn("criar o cômodo «corredor» (largura 1 m, comprimento 3 m)", r)

    def test_ficha_ilegivel_avisa(self):
        r = G.resumo_do_comando(f"{PY} -m director fazer sala nao_existe.json", tempfile.gettempdir())
        self.assertIn("Não consegui ler a ficha", r)

    def test_gancho(self):
        self.assertIsNone(G._antes_da_ferramenta("terminal", {"command": f"{PY} -m director estado sala"}))
        a = G._antes_da_ferramenta("terminal", {"command": f"{PY} -m director fazer sala x.json", "workdir": "C:/x"})
        b = G._antes_da_ferramenta("terminal", {"command": f"{PY} -m director fazer sala x.json", "workdir": "C:/x"})
        self.assertEqual(a["action"], "approve")
        self.assertNotEqual(a["rule_key"], b["rule_key"])  # "sempre aprovar" não vale para o próximo
        m = G._antes_da_ferramenta("clarify", {"questions": '[{"question": "Q?"}]'})
        self.assertEqual(m, {"action": "modify", "args": {"questions": [{"question": "Q?"}]}})
        self.assertIsNone(G._antes_da_ferramenta("read_file", {"path": "x"}))


if __name__ == "__main__":
    unittest.main()
