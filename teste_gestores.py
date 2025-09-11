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

    # default: martingale
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

# 🔹 Teste com volatilidade baixa
gestor = criar_gestor(config, volatilidade=0.0003)
print("Stake inicial:", gestor.get_stake())
gestor.registrar_resultado("loss", payout=0, stake_executada=1.0)
print("Stake após loss:", gestor.get_stake())
gestor.registrar_resultado("win", payout=1.8, stake_executada=1.0)
print("Stake após win:", gestor.get_stake())

print("\n---\n")

# 🔹 Teste com volatilidade alta
gestor = criar_gestor(config, volatilidade=0.001)
print("Stake inicial:", gestor.get_stake())
gestor.registrar_resultado("loss", payout=0, stake_executada=1.0)
print("Stake após loss:", gestor.get_stake())
gestor.registrar_resultado("loss", payout=0, stake_executada=gestor.get_stake())
print("Stake após segundo loss:", gestor.get_stake())
gestor.registrar_resultado("win", payout=gestor.get_stake()*1.8, stake_executada=gestor.get_stake())
print("Stake após win:", gestor.get_stake())
