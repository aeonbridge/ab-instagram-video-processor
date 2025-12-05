#!/usr/bin/env python3
"""
Agendador de Monitoramento de Tendências
Executa o agente de monitoramento em intervalos regulares.

Requer:
    pip install schedule
"""

import os
import sys
import time
import schedule
from datetime import datetime
from pathlib import Path
from trend_monitor_agent import TrendMonitorAgent


class TrendMonitorScheduler:
    """Agendador para execução periódica do monitoramento."""

    def __init__(self, config_file: str = None, interval_hours: int = 6):
        """
        Inicializa o agendador.

        Args:
            config_file: Arquivo de configuração do agente
            interval_hours: Intervalo entre execuções em horas
        """
        self.config_file = config_file
        self.interval_hours = interval_hours
        self.agent = TrendMonitorAgent(config_file=config_file)
        self.run_count = 0

    def run_monitoring(self):
        """Executa uma coleta de monitoramento."""
        self.run_count += 1

        print("\n" + "="*80)
        print(f"EXECUÇÃO #{self.run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        try:
            # Reinicializa coletores (caso necessário)
            self.agent.initialize_collectors()

            # Coleta dados
            data = self.agent.collect_all()

            if data:
                # Salva com timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{self.agent.config['topic']}_trends_{timestamp}.csv"
                self.agent.save_to_csv(data, filename=filename)

                # Gera relatório
                self.agent.generate_report(data)

                print(f"\nPróxima execução em {self.interval_hours} hora(s)...")
            else:
                print("\nNenhum dado coletado nesta execução.")

        except Exception as e:
            print(f"\nErro durante execução: {e}")
            import traceback
            traceback.print_exc()

    def start(self):
        """Inicia o agendamento."""
        print("="*80)
        print("AGENDADOR DE MONITORAMENTO DE TENDÊNCIAS")
        print("="*80)
        print(f"\nTópico: {self.agent.config['topic']}")
        print(f"Intervalo: {self.interval_hours} hora(s)")
        print(f"Diretório de saída: {self.agent.config.get('output_dir', 'trend_data')}")
        print("\nPressione Ctrl+C para parar\n")

        # Executa imediatamente
        print("Executando primeira coleta...")
        self.run_monitoring()

        # Agenda execuções futuras
        schedule.every(self.interval_hours).hours.do(self.run_monitoring)

        # Loop principal
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
        except KeyboardInterrupt:
            print("\n\nAgendador interrompido pelo usuário.")
            print(f"Total de execuções: {self.run_count}")


def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(description='Agendador de Monitoramento de Tendências')
    parser.add_argument('--config', type=str, help='Arquivo de configuração JSON')
    parser.add_argument('--topic', type=str, help='Tópico a monitorar')
    parser.add_argument('--interval', type=int, default=6, help='Intervalo em horas (padrão: 6)')

    args = parser.parse_args()

    # Inicializa agendador
    scheduler = TrendMonitorScheduler(
        config_file=args.config,
        interval_hours=args.interval
    )

    # Sobrescreve tópico se fornecido
    if args.topic:
        scheduler.agent.config['topic'] = args.topic

    # Inicia
    scheduler.start()


if __name__ == '__main__':
    main()
