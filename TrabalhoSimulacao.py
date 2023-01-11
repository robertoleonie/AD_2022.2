import random                       # Biblioteca - Números Aleatórios
import simpy                        # Biblioteca - Simulação
import numpy                        # Biblioteca - Computação Científica
import scipy.stats                  # Bilbioteca - Funções Estatísticas

#--------------------------------------------------------------------------
#Simulador
#--------------------------------------------------------------------------

# Funcao que cria as chegadas de clientes na Fila 1
def clientes_fila_1(env):

    global n_chegadas_1            # Numero total de chegadas a Fila 1
    global n_rodadas               # Numero de rodadas na fase de equilibrio

    global est_media               # Estimador da media mu chapeu
    global covariancia             # Covariancia
    global variancia               # Variancia estimada

    global transiente              # Booleano se esta na transiente (True) ou equilibrio (False)
    global terminado               # Booleano se o programa esta apto (True) para encerrar ou nao (False)
    global i_equilibrio            # Numero de "rodadas descartadas" ate que se chegue a fase de equilibrio

    # Enquanto o programa nao acabar
    while not(terminado):

        u = random.uniform(0,1)     # Geracao de v.a. uniforme U(0,1)
        x = numpy.log(1 - u)        # X = -ln(1-u)/lambda
        x /= (-1)*taxa_lambda
        
        # Aguarda um intervalo de tempo :
        # O tempo entre chegadas é exponencialmente distribuído
        W10.append(env.now)         # Coloca os instantes de chegada em uma lista
        yield env.timeout(random.expovariate(1.0/taxa_lambda))      # Envia a chegada Poisson para a rotina de serviço

        # Cada novo cliente eh uma nova rodada
        n_chegadas_1 += 1

        # Cada novo cliente eh uma nova rodada na fase de equilibrio
        # Se esta na fase de equilibrio, incrementa o numero de rodadas
        if not(transiente):
            n_rodadas += 1
            print("\n")
            print("------------------------------------")
            print("RODADA", n_rodadas)
            print("------------------------------------")

        # Tempo em que o novo cliente chega na fila
        print('[%.1f] FILA 1: Chegada do cliente %d' % (env.now, n_chegadas_1))
            
        # Atribui prioridade ao cliente (Prioridade Alta)
        prioridade, prio = "P1", 1
        print("[%.1f] FILA 1: Cliente %i com prioridade %s" %(env.now, n_chegadas_1, prioridade))


        # Determina a Variancia e Covariancia dos valores da Fila 1
        if(n_chegadas_1 > 2):
            est_media += W10[-1]/n_chegadas_1                                   # Calculo do estimador da media de forma incremental mu_chapeu = somatorio de i=1 a n Xi/n
            
            for i in range(1, n_chegadas_1):
                covariancia += (W10[-2] - est_media)*(W10[-1] - est_media)      # Covariancia sendo calculada de forma incremental
                covariancia *= 1/(n_chegadas_1 - 2)                             # Cov(ultimos dois instantes de chegada) = Somatorio de i=1 a n-1 de (Xi-mu_chapeu)*(Xi+1 - mu_chapeu)/(n-2)
            
            variancia += ((W10[-1] - est_media)**2)/(n_chegadas_1 - 1)          # Variancia (incremental) = Somatorio de i=1 a n de (X_i - mu_chapeu)^2 / (n-1)
        
        # Garante que a variancia eh pequena o bastante em relacao a covariancia em ordem de terminar a fase transiente
        # pequena = 100 vezes menor
        # se esta na fase transiente, queremos que ela encerre. Mas o calculo so permite mensurar a covariancia para numero de chegadas maior do que 2
        if((n_chegadas_1 > 2) and (transiente)):
            if(covariancia <= variancia/100):
                print("===============================================")
                print("FIM DA FASE TRANSIENTE - ENTRANDO NA FASE DE EQUILIBRIO")
                print("===============================================")
                transiente = False
                i_equilibrio = n_chegadas_1 # O total de chegadas que havia ocorrido eh o novo ponto de partida quando se esta agora na fase de equilibrio

        # Valor maximo de clientes aceito
        # IC calculado usando t-Student
        if ((2 * 1.96 * ((variancia)**(1.0/2.0)))/n_chegadas_1**(1.0/2.0) < 0.10*est_media ):
            terminado = True

        # Inicia o processo de atendimento
        env.process(atendimento_servidor(env, "FILA 1: Cliente %i" %n_chegadas_1, prioridade, prio, servico, "F1", 0))


# Funcao que cria as chegadas de clientes na Fila 2
def clientes_fila_2(env, tempoAtendimento):

    # Numero de chegadas a fila 2
    global n_chegadas_2

    # Se chega um cliente a fila 2, incrementa
    n_chegadas_2 += 1
    print('[%.1f] FILA 2: Chegada do cliente %d' % (env.now, n_chegadas_2))
    # Coloca seu instante de chegada na estrutura lista
    W20.append(env.now)

    # Atribui prioridade (Prioridade Baixa ou menor que a prioridade da fila 1)
    prioridade, prio = "P2", 2
    print("[%.1f] FILA 2: Cliente %i com prioridade %s" %(env.now, n_chegadas_2, prioridade))

    # Inicia o processo de atendimento
    env.process(atendimento_servidor(env, "FILA 2: Cliente %i" %n_chegadas_2, prioridade, prio, servico, "F2", tempoAtendimento))


# Funcao que ocupa o servidor e realiza o atendimento dos clientes
def atendimento_servidor(env, nome_cliente, prioridade, prio, servico, fila, tempoAtendimento):

    x = 0   # Variavel de controle interna
    # Ocupa 1 servidor
    with servico.request(priority=prio) as req:                         # Solicita o recurso servidorRes 
        yield req                                                       # Aguarda em fila até a liberação do recurso e o ocupa
        print("[%.1f] %s com %s inicia o atendimento" %(env.now, nome_cliente, prioridade))     # Cliente inicia o atendimento

        # Valores usados para calcular W1F e X10
        inicioAtendimento = env.now

        # Se for a vez do cliente da fila 1, ele nao precisa mais esperar
        # Append seu instante de abandono da fila 1 de espera
        # Append (em outra lista) seu instante de entrada em servico tambem
        if(fila == "F1"):
            W1F.append(env.now)
            X10.append(env.now)

        # Se for a vez do cliente da fila 2, ele nao precisa mais esperar
        # Append seu instante de abandono da fila 2 de espera
        # Append (em outra lista) seu instante de entrada em servico tambem
        if(fila == "F2"):
            W2F.append(env.now)
            X20.append(env.now)
            
        try:
            yield env.timeout(random.expovariate(1.0/taxa_mu))                                          # Aguarda um tempo de atendimento exponencialmente distribuído
            print("[%.1f] %s com %s termina o atendimento" %(env.now, nome_cliente, prioridade))        # Cliente termina o atendimento (Fila 1 ou Fila 2 sem bloqueio)

            if(prio == 1):                                                                              # Cliente da Fila 1 vai para a fila 2
                print("[%.1f] %s vai para a Fila 2" %(env.now, nome_cliente))

                # Guarda em uma estrutura lista o instante de termino de servico X1 do cliente
                X1F.append(env.now)

                # Chama o cliente recem encerrado de servico X1 para a fila 2
                clientes_fila_2(env, tempoAtendimento)
            else:                                                                                       # Cliente da Fila 2 sai das filas
                print("[%.1f] %s sai das filas" %(env.now, nome_cliente))

                #Valores usados para calcular X2F (com e sem interrupcao)
                if(tempoAtendimento == 0):                                                              # X2F - Sem interrupcao
                    X2F.append(env.now)
                else:                                                                                   # X2F - Com interrupcao
                    tempoAtendimento += env.now - inicioAtendimento                                     # Calcula o tempo de atendimento incrementalmente
                    tempoAtendimento = tempoAtendimento + X20[-1]
                    X2F.append(tempoAtendimento)                                                        # Apos o termino do servico X2 pelo cliente, guarda em uma estrutura lista

                x = 1
                yield servico.release(request)                                                          # Libera o recurso "servico"           
        except:                                                                                         # Cliente da fila 2 é bloqueado por cliente da fila 1
            if(x == 0):
                print("[%.1f] %s com %s tem atendimento interrompido" %(env.now, nome_cliente, prioridade)) # Cliente da fila 2 é interrompido
                tempoAtendimento += env.now - inicioAtendimento
                prio -= 0.001                                                                            # Prioridade < 2: Cliente da Fila 2 sera atendido assim que o servidor liberar
                env.process(atendimento_servidor(env, nome_cliente, prioridade, prio, servico, "F0", tempoAtendimento))
            else:
                x = 0

#--------------------------------------------------------------------------
# Inicia o simulador
#--------------------------------------------------------------------------

while(True):

    print("===============================================")
    print("SIMULADOR DE FILAS M/M/1 FCFS COM INTERRUPCAO")
    print("Metodo Batch")
    print("===============================================")
    p = float(input('Valor de utilizacao rho (p): '))
    print("===============================================")
    print("\n")

    taxa_lambda = p/2.0                 # Taxa de chegada Poisson (lambda = rho/2)
    taxa_mu = 1.0/60.0                  # Taxa de serviço mi

    n_chegadas_1 = 0                    # Numero de Clientes que entraram na fila 1
    n_chegadas_2 = 0                    # Numero de Clientes que entraram na fila 2
    n_rodadas = 0

    est_media = 0                       # Estimador da media mu_chapeu
    covariancia = 0                     # Covariancia inicializada
    variancia = 0                       # Variancia inicializada


    transiente = True                   # Booleano de fase transiente
    terminado = False                   # Booleano se o programa ja pode acabar
    i_equilibrio = 0                    # Contador de inicio da fase de equilibrio

    W10 = []                            # Lista de instantes de chegada de clientes na fila de espera 1
    W1F = []                            # Lista de instantes de partida de clientes na fila de espera 1
    W20 = []                            # Lista de instantes de chegada de clientes na fila de espera 2
    W2F = []                            # Lista de instantes de partida de clientes na fila de espera 2

    X10 = []                            # Lista de instantes de inicio de servico X1
    X1F = []                            # Lista de instantes do termino de servico X1
    X20 = []                            # Lista de instantes de inicio de servico X2
    X2F = []                            # Lista de instantes de termino de servico X2

    env = simpy.Environment()                                   # Cria o environment do modelo de simulacao
    servico = simpy.PreemptiveResource(env, capacity=1)         # Cria o recurso servidorRes
    env.process(clientes_fila_1(env))                           # Inicia o processo de geração de chegadas
    env.run()                                                   # Realiza a execucao do simulador


    print("===============================================")
    print("FECHADO - FIM DA SIMULACAO")
    print("===============================================")

    print("Insira 0 para sair do programa")
    print("Insira 1 para ver a tabela com as metricas obtidas")
    print("Insira qualquer outro valor para reiniciar o programa")
    x = float(input())                                          # Variavel de menu

    # Se x = 0, encerra o programa
    if(x == 0):
        exit()

    # Se x = 1, imprime a tabela das metricas
    if(x == 1):
        EX1 = 0         # Tempo Medio de Servico na Fila 1
        EX2 = 0         # Tempo Medio de Servico da Fila 2
    
        EW1 = 0         # Tempo Medio de Espera na Fila 1
        EW2 = 0         # Tempo Medio de Espera da Fila 2

        EW1_2 = 0       # Segundo Momento de Espera da Fila 1
        EW2_2 = 0       # Segundo Momento de Espera da Fila 2

        VW1 = 0         # Variancia de Espera da Fila 1
        VW2 = 0         # Variancia de Espera da Fila 2

        for i in range (0, n_rodadas) :
            ET1 = 0     # Tempo Medio Total Gasto na Fila 1
            ET2 = 0     # Tempo Medio Total Gasto na Fila 2

            print("------------------------------------")
            print("RODADA", i+1)
            print("------------------------------------")


            # Utilizando a partir de i_equilibrio pois descartamos
            # os dados da fase transiente

            # E[W1] = Tempo medio na fila de espera 1
            EW1 += W1F[i_equilibrio + i] - W10[i_equilibrio + i]                # E[W1] = Instante de termino na fila de espera 1 - Instante de inicio na fila de espera 1
            EW1 /= (i+1)                                                        # dividindo tudo pelo numero de rodadas da fase de equilibrio

            # E[W2] = Tempo medio na fila de espera 2
            EW2 += W2F[i_equilibrio + i] - W20[i_equilibrio + i]                # E[W2] = Instante de termino na fila de espera 2 - Instante de inicio na fila de espera 2
            EW2 /= (i+1)                                                        # dividindo tudo pelo numero de rodadas da fase de equilibrio

            # Para calcular a variancia ao final, precisamos obter os segundos momentos
            # E[W1^2] = Segundo momento do tempo de espera na fila 1
            EW1_2 += (W1F[i_equilibrio + i] - W10[i_equilibrio + i])**2         # No fundo, o segundo momento de uma v.a. eh elevar qualquer v.a. dependente ao quadrado
            EW1_2 /= (i+1)                                                      # Mesmo procedimento que foi realizado para E[W1]

            # E[W2^2] = Segundo momento do tempo de espera na fila 2
            EW2_2 += (W1F[i_equilibrio + i] - W10[i_equilibrio + i])**2         # Mesmo procedimento que foi realizado para E[W2]
            EW2_2 /= (i+1)

            # E[X1] = Tempo medio de servico para a fila 1
            EX1 += X1F[i_equilibrio + i] - X10[i_equilibrio + i]                # E[X1] = Instante de termino de servico da fila 1 - Instante de inicio de servico da fila 1
            EX1 /= (i+1)                                                        # Para obter a media, divide pelo numero de rodadas da fase de equilibrio

            # E[X2] = Tempo medio de servico para a fila 2
            EX2 += X2F[i_equilibrio + i] - X20[i_equilibrio + i]                # E[X2] = Instante de termino de servico da fila 2 - Instante de inicio de servico da fila 2
            EX2 /= (i+1)                                                        # Para obter a media, divide pelo numero de rodadas da fase de equilibrio

            ET1 = EW1 + EX1                                                     # Calculo do Tempo medio total gasto na fila 1 E[T1] = E[W1] + E[X1] 
            ET2 = EW2 + EX2                                                     # Calculo do Tempo medio total gasto na fila 2 E[T2] = E[W2] + E[X2] 

            VW1 += EW1_2 - EW1**2                                               # Calculo da Variancia do Tempo de Espera na Fila 1: Var(W1) = E[W1^2] - E[W1]^2
            VW2 += EW2_2 - EW2**2                                               # Calculo da Variancia do Tempo de Espera na Fila 1: Var(W2) = E[W2^2] - E[W2]^2

            # Imprimindo a tabela com as metricas obtidas
            print("E[W1] = %f" % (EW1))
            print("E[W2] = %f" % (EW2))
            print("E[X1] = %f" % (EX1))
            print("E[X2] = %f" % (EX2))
            print("E[T1] = %f" % (ET1))
            print("E[T2] = %f" % (ET2))
            print("Var(W1) = %f" % (VW1))
            print("Var(W2) = %f" % (VW2))
            
        print("===============================================")
        print("\n\n")
                        
