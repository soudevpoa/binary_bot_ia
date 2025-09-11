class EstrategiaMM:
    def __init__(self, periodo_curto, periodo_longo):
        self.periodo_curto = periodo_curto
        self.periodo_longo = periodo_longo

    def decidir(self, prices):
        mm_curta = sum(prices[-self.periodo_curto:]) / self.periodo_curto
        mm_longa = sum(prices[-self.periodo_longo:]) / self.periodo_longo

        if mm_curta > mm_longa:
            return "CALL", mm_curta, mm_longa
        elif mm_curta < mm_longa:
            return "PUT", mm_curta, mm_longa
        return None, mm_curta, mm_longa
    