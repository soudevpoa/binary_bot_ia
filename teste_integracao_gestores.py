import random
from core.gestores.stake_fixa import StakeFixa
from core.gestores.soros import Soros
from core.martingale_inteligente import MartingaleInteligente

# Simula o método _criar_gestor do BotBase
def criar_gestor(config, volatilidade=None):
    modo = config.get("modo_operacao", "martingale")
    stake_base = float(config.get("stake_base", 1.0))
    stake_max = config.get("stake_max")

    if modo == "fixo":
        fixo_cfg = config.get("fixo", {})
        return StakeFixa(fixo_cfg.get("valor", stake_base))

    if modo == "soros":
        soros_cfg = config.get("soros", {})
        return Soros(
            stake_base=stake_base,
            max_niveis=soros_cfg.get("max_niveis", 2),
            reinvestir=soros_cfg.get("reinvestir", "lucro"),
            stake_max=stake_max
        )

    if modo == "dinamico":
        cfg = config.get("dinamico", {})
        limiar = cfg.get("limiar_volatilidade", 0.0005)
        if volatilidade is not None and volatilidade < limiar:
            print("📉 Volatilidade baixa → usando FIXO")
            return StakeFixa(cfg.get("fixo_valor", stake_base))
        else:
            print("📈 Volatilidade alta → usando MARTINGALE")
            return MartingaleInteligente(
                stake_base=stake_base,
                max_niveis=cfg.get("martingale_max_niveis", config.get("max_niveis", 3)),
                fator_multiplicador=cfg.get("martingale_fator", config.get("fator_multiplicador", 2.0)),
                stake_max=stake_max
            )

    return MartingaleInteligente(
        stake_base=stake_base,
        max_niveis=config.get("max_niveis", 3),
        fator_multiplicador=config.get("fator_multiplicador", 2.0),
        stake_max=stake_max
    )

# Config de teste
config = {
    "modo_operacao": "dinamico",
    "stake_base": 1.0,
    "max_niveis": 3,
    "fator_multiplicador": 2.0,
    "fixo": {"valor": 1.0},
    "soros": {"max_niveis": 2, "reinvestir": "lucro"},
    "dinamico": {
        "limiar_volatilidade": 0.0005,
        "baixo_volatilidade": "fixo",
        "alto_volatilidade": "martingale",
        "fixo_valor": 1.0,
        "martingale_max_niveis": 2,
        "martingale_fator": 1.8
    }
}

# 🔹 Simulação de 10 operações
for i in range(1, 11):
    volatilidade = round(random.uniform(0.0001, 0.001), 6)
    gestor = criar_gestor(config, volatilidade=volatilidade)

    stake = gestor.get_stake()
    resultado = random.choice(["win", "loss"])
    payout = round(stake * random.uniform(1.7, 1.95), 2) if resultado == "win" else 0.0

    print(f"\n🎯 Operação {i}")
    print(f"📊 Volatilidade: {volatilidade} | Stake inicial: {stake}")
    print(f"Resultado: {resultado} | Payout: {payout}")

    gestor.registrar_resultado(resultado, payout=payout, stake_executada=stake)
    print(f"💰 Próxima stake: {gestor.get_stake()}")
