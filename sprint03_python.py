from datetime import datetime
import csv
import os
import time
import random

PRECO_KWH_NORMAL = 1.97
PRECO_KWH_PICO = 2.25
TARIFA_SESSAO = 0.89
POTENCIA_MAXIMA = 100


LIMITE_MIN_BATERIA = 25.0
CUSTO_KWH_RENOVAVEL = 0.05
FATOR_CO2_KG_POR_KWH = 0.12

usuarios = {}
usuario_logado = None
sessoes = []


estado_bateria = {"nivel_pct": 60.0}


def cadastrar_usuario():
    global usuario_logado
    nome = input("Nome: ").strip()
    email = input("Email: ").strip().lower()

    if not nome or not email:
        print("Dados inválidos.")
        return

    if email not in usuarios:
        usuarios[email] = {
            "nome": nome,
            "email": email,
            "pontos": 0
        }

    usuario_logado = email
    print(f"\nLogin automático realizado. Bem-vindo(a), {nome}!")


def obter_tarifa():
    hora = datetime.now().hour
    return PRECO_KWH_PICO if 18 <= hora <= 22 else PRECO_KWH_NORMAL


def assistente_ia():
    hora = datetime.now().hour
    energia_solar = random.randint(10, 30)

    if 18 <= hora <= 22:
        ocupacao = "Alta"
        demanda = "Alta"
    elif 12 <= hora <= 17:
        ocupacao = "Média"
        demanda = "Média"
    else:
        ocupacao = "Baixa"
        demanda = "Baixa"

    economia = energia_solar * 0.40

    print("\n===== Assistente IA =====")
    print(f"Demanda prevista: {demanda}")
    print(f"Ocupação prevista: {ocupacao}")
    print(f"Energia solar disponível: {energia_solar} kWh")
    print(f"Economia estimada: R$ {economia:.2f}")

    if demanda == "Alta":
        print("Recomendação: aguarde fora do horário de pico.")
    else:
        print("Recomendação: ótimo momento para recarregar.")

    return energia_solar


def simular_dlm():
    try:
        qtd = int(input("Quantidade de veículos conectados: "))
        if qtd <= 0:
            return
    except:
        print("Valor inválido.")
        return

    baterias = []
    pesos = []

    for i in range(qtd):
        carga = float(input(f"Carga atual do Veículo {i+1} (%): "))
        peso = max(1, 100 - carga)
        baterias.append(carga)
        pesos.append(peso)

    soma_pesos = sum(pesos)

    print("\n===== DLM Inteligente =====")
    for i in range(qtd):
        potencia = POTENCIA_MAXIMA * (pesos[i] / soma_pesos)
        print(f"Veículo {i+1} ({baterias[i]}%) -> {potencia:.2f} kWh")


def decidir_fonte_energia(energia_solar_kw, demanda_kw, bateria_pct, hora):
    solar_suficiente = energia_solar_kw >= demanda_kw
    bateria_disponivel = bateria_pct > LIMITE_MIN_BATERIA
    horario_de_pico = 18 <= hora <= 22

    usar_solar = solar_suficiente
    usar_bateria = (not solar_suficiente) and bateria_disponivel
    usar_rede = (not solar_suficiente) and (not bateria_disponivel)

    if usar_solar:
        return "Solar"
    elif usar_bateria:
        return "Bateria"
    elif usar_rede and horario_de_pico:
        return "Rede Pico"
    else:
        return "Rede Normal"


def acionar_automacao(fonte):
    comandos = {
        "Solar":       "Solar=ON  | Bateria=OFF | Rede=OFF",
        "Bateria":     "Solar=OFF | Bateria=ON  | Rede=OFF",
        "Rede Normal": "Solar=OFF | Bateria=OFF | Rede=ON   (tarifa normal)",
        "Rede Pico":   "Solar=OFF | Bateria=OFF | Rede=ON   (tarifa de pico)",
    }
    comando = comandos[fonte]
    print(f"    [Automação] {comando}")
    return comando


def atualizar_bateria(fonte, energia_solar_kw, demanda_kw):
    """Atualiza o nível do sistema de armazenamento após a decisão."""
    if fonte == "Solar" and energia_solar_kw > demanda_kw:
        sobra = energia_solar_kw - demanda_kw
        estado_bateria["nivel_pct"] = min(100.0, estado_bateria["nivel_pct"] + sobra)
    elif fonte == "Bateria":
        estado_bateria["nivel_pct"] = max(0.0, estado_bateria["nivel_pct"] - demanda_kw * 1.5)
    else:
        estado_bateria["nivel_pct"] = min(100.0, estado_bateria["nivel_pct"] + 0.3)


def iniciar_recarga():
    global usuario_logado

    try:
        energia = float(input("Energia desejada (kWh): "))
        if energia <= 0:
            return
    except:
        print("Valor inválido.")
        return

    hora = datetime.now().hour
    energia_solar_kw = round(random.uniform(5, 30), 2)

    fonte = decidir_fonte_energia(energia_solar_kw, energia, estado_bateria["nivel_pct"], hora)
    comando = acionar_automacao(fonte)
    atualizar_bateria(fonte, energia_solar_kw, energia)

    if fonte == "Solar":
        energia_solar_utilizada = energia
        energia_rede = 0.0
        valor = energia * CUSTO_KWH_RENOVAVEL + TARIFA_SESSAO
    elif fonte == "Bateria":
        energia_solar_utilizada = 0.0
        energia_rede = 0.0
        valor = energia * CUSTO_KWH_RENOVAVEL + TARIFA_SESSAO
    else:
        energia_solar_utilizada = 0.0
        energia_rede = energia
        valor = energia_rede * obter_tarifa() + TARIFA_SESSAO

    print("\n1 - Pix")
    print("2 - Cartão")
    print("3 - QR Code")

    opc = input("Pagamento: ")
    pagamento = {"1": "PIX", "2": "Cartão", "3": "QR Code"}.get(opc, "Não informado")

    print(f"\nFonte de energia definida pela automação: {fonte}")
    print("Iniciando recarga...")

    inicio = datetime.now()

    for i in range(10):
        time.sleep(0.2)
        print(f"Carregando... {(i+1)*10}%")

    duracao = round((datetime.now() - inicio).total_seconds()/60, 2)

    usuario = "Visitante"
    pontos = 0

    if usuario_logado:
        usuario = usuarios[usuario_logado]["nome"]
        pontos = int(valor/5)
        usuarios[usuario_logado]["pontos"] += pontos

    co2 = energia * FATOR_CO2_KG_POR_KWH if fonte in ("SOLAR", "BATERIA") else 0.0

    sessao = {
        "usuario": usuario,
        "energia": energia,
        "solar": energia_solar_utilizada,
        "rede": energia_rede,
        "valor": valor,
        "pagamento": pagamento,
        "co2": co2,
        "duracao": duracao,
        "data": datetime.now(),
        "fonte": fonte,                  # NOVO NA SPRINT 3
        "comando_automacao": comando,    # NOVO NA SPRINT 3
    }

    sessoes.append(sessao)

    print("\n===== Recarga finalizada =====")
    print(f"Usuário: {usuario}")
    print(f"Fonte utilizada: {fonte}")
    print(f"Valor pago: R$ {valor:.2f}")
    print(f"Pontos ganhos: {pontos}")
    print(f"CO₂ evitado: {sessao['co2']:.2f} kg")


def consultar_pontos():
    if not usuario_logado:
        print("Nenhum usuário cadastrado/logado.")
        return

    print(f"Usuário: {usuarios[usuario_logado]['nome']}")
    print(f"Pontos: {usuarios[usuario_logado]['pontos']}")


def historico():
    if not sessoes:
        print("Nenhuma sessão registrada.")
        return

    print("\n===== Histórico geral =====")

    for i, s in enumerate(sessoes, start=1):
        print(f"\nSessão #{i}")
        print(f"Usuário: {s['usuario']}")
        print(f"Data: {s['data'].strftime('%d/%m/%Y %H:%M')}")
        print(f"Energia: {s['energia']:.2f} kWh")
        print(f"Fonte: {s.get('fonte', 'N/D')}")
        print(f"Valor: R$ {s['valor']:.2f}")
        print(f"Pagamento: {s['pagamento']}")


def dashboard():
    energia_total = sum(s["energia"] for s in sessoes)
    energia_solar = sum(s["solar"] for s in sessoes)
    receita = sum(s["valor"] for s in sessoes)
    co2 = sum(s["co2"] for s in sessoes)

    print("\n===== Dashborad =====")
    print(f"Sessões: {len(sessoes)}")
    print(f"Energia Total: {energia_total:.2f} kWh")
    print(f"Energia Solar: {energia_solar:.2f} kWh")
    print(f"Receita: R$ {receita:.2f}")
    print(f"CO₂ Evitado: {co2:.2f} kg")
    print(f"Nível atual da bateria: {estado_bateria['nivel_pct']:.1f}%")


def simulacao_carga():
    try:
        bateria = float(input("Capacidade da bateria (kWh): "))
        carga = float(input("Carga atual (%): "))

        energia = bateria * (100 - carga) / 100
        autonomia = energia * 6

        print(f"Energia necessária: {energia:.2f} kWh")
        print(f"Autonomia estimada: {autonomia:.0f} km")
    except:
        print("Valores inválidos.")


def exportar_dados_csv(caminho="sessoes_recarga.csv"):
    if not sessoes:
        print("Nenhuma sessão para exportar.")
        return None

    campos = ["usuario", "energia", "solar", "rede", "valor", "pagamento",
              "co2", "duracao", "data", "fonte", "comando_automacao"]

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        for s in sessoes:
            linha = dict(s)
            linha["data"] = s["data"].strftime("%Y-%m-%d %H:%M:%S")
            linha["fonte"] = s.get("fonte", "N/D")
            linha["comando_automacao"] = s.get("comando_automacao", "N/D")
            escritor.writerow(linha)

    print(f"Dados exportados para '{caminho}' ({len(sessoes)} sessões).")
    return caminho


def demo_integrado_sprint3(n_veiculos=5):
    print("\n===== PROTÓTIPO INTEGRADO - SPRINT 3 =====")
    print("Assistente de IA (previsão) + DLM (distribuição) + Lógica booleana + Automação\n")

    hora = datetime.now().hour
    energia_solar_kw = assistente_ia()
    solar_restante_kw = energia_solar_kw  # NOVO: geração solar é consumida ao longo da rodada

    baterias_veiculos = [round(random.uniform(10, 90), 1) for _ in range(n_veiculos)]
    pesos = [max(1, 100 - b) for b in baterias_veiculos]
    soma_pesos = sum(pesos)

    print("\nDistribuindo potência entre veículos (menor carga = maior prioridade):")

    for i in range(n_veiculos):
        potencia_alocada = round(POTENCIA_MAXIMA * (pesos[i] / soma_pesos), 2)
        demanda_kw = potencia_alocada

        fonte = decidir_fonte_energia(solar_restante_kw, demanda_kw, estado_bateria["nivel_pct"], hora)
        comando = acionar_automacao(fonte)
        atualizar_bateria(fonte, solar_restante_kw, demanda_kw)

        if fonte == "Solar":
            solar_restante_kw = max(0.0, solar_restante_kw - demanda_kw)

        renovavel = fonte in ("Solar", "Bateria")
        valor = demanda_kw * CUSTO_KWH_RENOVAVEL if renovavel else demanda_kw * obter_tarifa()
        co2 = demanda_kw * FATOR_CO2_KG_POR_KWH if renovavel else 0.0

        print(f"  Veículo {i+1}: carga={baterias_veiculos[i]}% | "
              f"potência alocada={potencia_alocada:.2f} kWh | fonte={fonte}")

        sessoes.append({
            "usuario": f"Veículo {i+1} (demo Sprint 3)",
            "energia": demanda_kw,
            "solar": demanda_kw if fonte == "SOLAR" else 0.0,
            "rede": demanda_kw if fonte.startswith("REDE") else 0.0,
            "valor": round(valor, 2),
            "pagamento": "Simulação",
            "co2": round(co2, 3),
            "duracao": 0,
            "data": datetime.now(),
            "fonte": fonte,
            "comando_automacao": comando,
        })

    print(f"\nNível da bateria de armazenamento após a rodada: "
          f"{estado_bateria['nivel_pct']:.1f}%")

    caminho = exportar_dados_csv()
    dashboard()
    return caminho


def main():
    while True:
        print("\n==========")
        print("ChargeVolt")
        print("==========")

        if usuario_logado:
            print(f"Usuário ativo: {usuarios[usuario_logado]['nome']}")
        else:
            print("Modo visitante")

        print("\n1 - Cadastrar usuário")
        print("2 - Iniciar recarga")
        print("3 - Consultar pontos")
        print("4 - Histórico")
        print("5 - Dashboard")
        print("6 - Assistente IA")
        print("7 - Simular DLM")
        print("8 - Simulação de carga")
        print("9 - Protótipo Integrado")
        print("10 - Exportar dados (CSV)")
        print("0 - Sair")

        op = input("Escolha: ")

        if op == "1":
            cadastrar_usuario()
        elif op == "2":
            iniciar_recarga()
        elif op == "3":
            consultar_pontos()
        elif op == "4":
            historico()
        elif op == "5":
            dashboard()
        elif op == "6":
            assistente_ia()
        elif op == "7":
            simular_dlm()
        elif op == "8":
            simulacao_carga()
        elif op == "9":
            demo_integrado_sprint3()
        elif op == "10":
            exportar_dados_csv()
        elif op == "0":
            break


if __name__ == "__main__":
    main()