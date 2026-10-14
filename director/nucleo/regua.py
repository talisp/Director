"""Réguas da primeira entrega: contas puras sobre o que o Unreal mediu. Cada uma tem o seu caso que reprova
(ver testes). Limites escritos antes de rodar, em docs/PEDIDO_ATUAL.md (13/10)."""
import math

LIM_MEDIDA_CM = 2.0  # A1, B: medida interna da sala
LIM_REPOUSO_CM = 1.0  # C: prato e copo não saem do lugar
QUEDA_MINIMA_CM = 50.0  # C: o copo fora da borda tem de cair pelo menos isto
LIM_CHEGADA_CM = 50.0  # A6: o personagem chega
LIM_MESMO_LUGAR_CM = 0.1  # B, D: "no mesmo lugar"
LIM_INCORPORAR_CM = 1.0  # E


def medida_interna(dist_a: float, dist_b: float, pedido_cm: float) -> dict:
    """Dois raios saem do mesmo ponto em sentidos opostos e batem em paredes opostas: a soma é a medida interna."""
    medido = dist_a + dist_b
    return {"ok": abs(medido - pedido_cm) <= LIM_MEDIDA_CM, "medido_cm": round(medido, 2), "pedido_cm": pedido_cm}


def repouso(antes: list, depois: list) -> dict:
    """O objeto ficou onde estava? (desceu e andou de lado, em cm)"""
    desceu = antes[2] - depois[2]
    andou = math.hypot(depois[0] - antes[0], depois[1] - antes[1])
    return {"ok": abs(desceu) <= LIM_REPOUSO_CM and andou <= LIM_REPOUSO_CM, "desceu_cm": round(desceu, 2), "andou_cm": round(andou, 2)}


def caiu(antes: list, depois: list) -> dict:
    desceu = antes[2] - depois[2]
    return {"ok": desceu >= QUEDA_MINIMA_CM, "desceu_cm": round(desceu, 2)}


def chegou(distancia_chao_cm: float, situacao: str, velocidade: float) -> dict:
    """Chegou = perto do destino, parado e com o movimento encerrado pelo Unreal."""
    return {"ok": distancia_chao_cm <= LIM_CHEGADA_CM and situacao.upper() == "IDLE" and velocidade < 5.0,
            "distancia_cm": round(distancia_chao_cm, 1), "situacao": situacao, "velocidade": velocidade}


def mesmo_lugar(a: list, b: list, limite: float = LIM_MESMO_LUGAR_CM) -> dict:
    d = math.dist(a[:3], b[:3])
    return {"ok": d <= limite, "distancia_cm": round(d, 3)}
