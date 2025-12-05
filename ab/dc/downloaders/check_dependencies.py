#!/usr/bin/env python3
"""
Script de verificação de dependências
Verifica se todas as dependências estão instaladas e fornece instruções
"""

import subprocess
import sys
import platform
from pathlib import Path


def check_command(cmd, name):
    """Verifica se um comando está disponível"""
    try:
        result = subprocess.run(
            [cmd, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # FFmpeg retorna a versão em stderr e código de saída não-zero
        # Outros comandos retornam em stdout com código 0
        output = result.stdout or result.stderr

        if output and (result.returncode == 0 or (cmd == 'ffmpeg' and output.startswith('ffmpeg'))):
            version = output.split('\n')[0] if output else "unknown version"
            print(f"  ✓ {name:20s} instalado ({version[:50]})")
            return True
        else:
            print(f"  ✗ {name:20s} não funciona corretamente (code: {result.returncode})")
            return False
    except FileNotFoundError:
        print(f"  ✗ {name:20s} NÃO encontrado")
        return False
    except Exception as e:
        print(f"  ✗ {name:20s} erro: {e}")
        return False


def check_python_package(package, import_name=None):
    """Verifica se um pacote Python está instalado"""
    if import_name is None:
        import_name = package

    try:
        __import__(import_name)
        print(f"  ✓ {package:20s} instalado")
        return True
    except ImportError:
        print(f"  ✗ {package:20s} NÃO encontrado")
        return False


def get_install_instructions():
    """Retorna instruções de instalação baseadas no sistema operacional"""
    os_name = platform.system()

    instructions = {
        'Darwin': {  # macOS
            'ffmpeg': [
                "Para instalar FFmpeg no macOS:",
                "",
                "1. Verifique se o Homebrew está instalado:",
                "   which brew",
                "",
                "2. Se não estiver, instale o Homebrew:",
                "   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
                "",
                "3. Instale o FFmpeg:",
                "   brew install ffmpeg",
                "",
                "4. Verifique a instalação:",
                "   ffmpeg -version"
            ],
            'yt-dlp': [
                "Para instalar yt-dlp:",
                "   pip install yt-dlp"
            ]
        },
        'Linux': {  # Ubuntu/Debian
            'ffmpeg': [
                "Para instalar FFmpeg no Linux:",
                "   sudo apt-get update",
                "   sudo apt-get install ffmpeg"
            ],
            'yt-dlp': [
                "Para instalar yt-dlp:",
                "   pip install yt-dlp"
            ]
        }
    }

    return instructions.get(os_name, instructions['Linux'])


def main():
    print("="*70)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("="*70)
    print()

    # Informações do sistema
    print("Sistema:")
    print(f"  OS: {platform.system()} {platform.release()}")
    print(f"  Python: {sys.version.split()[0]}")
    print()

    # Verificar dependências do sistema
    print("Dependências do Sistema:")
    ffmpeg_ok = check_command('ffmpeg', 'FFmpeg')
    ytdlp_ok = check_command('yt-dlp', 'yt-dlp')
    brew_ok = None

    if platform.system() == 'Darwin':  # macOS
        brew_ok = check_command('brew', 'Homebrew')

    print()

    # Verificar pacotes Python
    print("Pacotes Python:")
    dotenv_ok = check_python_package('python-dotenv', 'dotenv')
    whisper_ok = check_python_package('openai-whisper', 'whisper')
    torch_ok = check_python_package('torch', 'torch')

    print()
    print("="*70)
    print("RESULTADO")
    print("="*70)
    print()

    # Análise dos resultados
    missing_deps = []

    if not ffmpeg_ok:
        missing_deps.append('FFmpeg')
    if not ytdlp_ok:
        missing_deps.append('yt-dlp')

    if missing_deps:
        print("❌ DEPENDÊNCIAS FALTANDO!")
        print()
        print("Serviços disponíveis com as dependências atuais:")

        if ytdlp_ok:
            print("  ✓ Subtitle Download Service (cli_subtitle.py)")

        if not ffmpeg_ok:
            print("  ✗ Video Clipper Service (requer FFmpeg)")
            print("  ✗ Subtitle Clipper Service (requer FFmpeg via video_clipper)")

        if not whisper_ok:
            print("  ✗ Video Transcription Service (requer openai-whisper)")

        print()
        print("="*70)
        print("INSTRUÇÕES DE INSTALAÇÃO")
        print("="*70)
        print()

        instructions = get_install_instructions()

        # Instruções específicas para o que está faltando
        if platform.system() == 'Darwin' and not brew_ok and not ffmpeg_ok:
            print("⚠️  ATENÇÃO: Homebrew não está instalado!")
            print()
            print("O Homebrew é necessário para instalar FFmpeg no macOS.")
            print("Instale primeiro o Homebrew, depois o FFmpeg.")
            print()
            print("\n".join(instructions['ffmpeg']))
            print()
        elif not ffmpeg_ok:
            print("📦 FFmpeg não está instalado")
            print()
            print("\n".join(instructions['ffmpeg']))
            print()

        if not ytdlp_ok:
            print("📦 yt-dlp não está instalado")
            print()
            print("\n".join(instructions['yt-dlp']))
            print()

        # Pacotes Python opcionais
        python_packages = []
        if not dotenv_ok:
            python_packages.append('python-dotenv')
        if not whisper_ok:
            python_packages.append('openai-whisper')
        if not torch_ok:
            python_packages.append('torch')

        if python_packages:
            print("📦 Pacotes Python opcionais:")
            print()
            print("   pip install " + " ".join(python_packages))
            print()

        print("="*70)
        print()
        print("💡 Dica: Consulte QUICK_INSTALL.md para guia passo a passo")
        print("         ou INSTALLATION.md para instruções detalhadas")
        print()

        return 1
    else:
        print("✅ TODAS AS DEPENDÊNCIAS NECESSÁRIAS ESTÃO INSTALADAS!")
        print()
        print("Você pode usar todos os serviços:")
        print("  ✓ Video Clipper Service")
        print("  ✓ Subtitle Download Service")
        print("  ✓ Subtitle Clipper Service")

        if whisper_ok:
            print("  ✓ Video Transcription Service")
        else:
            print("  ℹ Video Transcription Service (instale openai-whisper e torch)")

        print()
        print("Exemplos de uso:")
        print("  python cli_subtitle.py list VIDEO_ID")
        print("  python cli_subtitle_clipper.py --video-id VIDEO_ID -l en")
        print("  python cli_clipper.py --video-id VIDEO_ID")
        print()

        return 0


if __name__ == '__main__':
    sys.exit(main())