import unittest
from director.veredito import com_veredito


def rota(nome, chegou=True, dist=5.0, parcial=False, bate=None):
    passagem = {"livre": bate is None, "segmentos": [{"acertou": True, **bate}] if bate else []}
    return {"nome": nome, "passagem": passagem, "caminho": {"existe": True, "parcial": parcial, "completo": not parcial},
            "destino_na_malha": not parcial, "personagem": {"executado": True, "chegou": chegou, "distancia_cm": dist}}


class Veredito(unittest.TestCase):
    def test_ok_true_com_aprovado_false_vira_reprovado_no_topo(self):
        # O caso real de 17/10: ok true, aprovado false, boneco a 424,8 cm do guarda-roupa.
        res = {"ok": True, "aprovado": False, "problemas": [], "possiveis_penetracoes_envelopes": [], "objetos": [{}],
               "circulacao": [rota("sala_ate_cama"), rota("sala_ate_guarda", chegou=False, dist=424.8, parcial=True)]}
        r = com_veredito("verificar", res)
        self.assertEqual(list(r)[:3], ["veredito", "motivo", "proxima_acao"])
        self.assertEqual(r["veredito"], "REPROVADO")
        self.assertIn("sala_ate_guarda: o boneco nao chegou (ficou a 424.8 cm", r["motivo"])
        self.assertNotIn("sala_ate_cama", r["motivo"])
        self.assertIn("NAO relatar como aprovado", r["proxima_acao"])
        self.assertTrue(r["ok"])  # nada medido muda

    def test_porta_so_quando_a_capsula_bate_numa_porta(self):
        base = {"ok": True, "aprovado": False, "objetos": [{}], "problemas": [], "possiveis_penetracoes_envelopes": []}
        r = com_veredito("verificar", {**base, "circulacao": [rota("porta_ate_cama", chegou=False, dist=15)]})
        self.assertNotIn("abra a porta", r["proxima_acao"])
        r = com_veredito("verificar", {**base, "circulacao": [rota("x", bate={"id": "porta_quarto", "rotulo": "porta_quarto", "tipo": "porta"})]})
        self.assertIn("abra a porta", r["proxima_acao"])
        self.assertIn("bate em porta_quarto (porta)", r["motivo"])

    def test_fisica_instavel_e_sem_objetos(self):
        res = {"ok": True, "aprovado": False, "objetos": [], "problemas": [], "possiveis_penetracoes_envelopes": [],
               "circulacao": [], "play": {"fisica": [{"ator": "box", "fisica": True, "estavel": False, "deslocamento_cm": 12}]}}
        r = com_veredito("verificar", res)
        self.assertIn("box: nao ficou parado", r["motivo"])
        self.assertIn("nenhum objeto", r["motivo"])

    def test_aprovado_e_planejamento(self):
        self.assertEqual(com_veredito("verificar", {"ok": True, "aprovado": True})["veredito"], "APROVADO")
        r = com_veredito("planejar", {"ok": True, "dimensoes_cm": [260, 350], "verificacao2d": {"criterio": "c"}})
        self.assertEqual(r["veredito"], "APROVADO")
        self.assertIn("ainda nao foi testada no Unreal", r["proxima_acao"])
        r = com_veredito("planejar", {"ok": False, "motivo": "filtro2d_reprovou", "detalhe": "3 arrumacoes reprovadas"})
        self.assertEqual((r["veredito"], r["motivo"], r["codigo"]), ("REPROVADO", "3 arrumacoes reprovadas", "filtro2d_reprovou"))
        self.assertIn("nao mude a cena", r["proxima_acao"])

    def test_erro_vira_erro(self):
        r = com_veredito("verificar", {"ok": False, "motivo": "erro", "porque": "TimeoutError: ponte"})
        self.assertEqual((r["veredito"], r["motivo"]), ("ERRO", "TimeoutError: ponte"))


if __name__ == "__main__":
    unittest.main()
