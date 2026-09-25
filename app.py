"""Extrator desktop para mídia própria e links autorizados."""
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse


def executable(name):
    bundled = Path(getattr(sys, '_MEIPASS', Path(__file__).parent)) / (name + '.exe')
    return str(bundled) if bundled.exists() else shutil.which(name)


def validated_url(raw):
    url = raw.strip()
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    domains = ('youtube.com', 'youtu.be', 'tiktok.com')
    if parsed.scheme != 'https' or not any(host == d or host.endswith('.' + d) for d in domains):
        raise ValueError('Use um link HTTPS do YouTube ou TikTok.')
    return url


def command_for(kind, source, output, mode):
    ffmpeg = executable('ffmpeg')
    if kind == 'Link':
        url = validated_url(source)
        cmd = [sys.executable, '-m', 'yt_dlp'] if not getattr(sys, 'frozen', False) else [sys.executable, '--yt-dlp']
        cmd += ['--no-playlist', '--restrict-filenames', '--paths', str(output), '--ffmpeg-location', str(Path(ffmpeg).parent)] if ffmpeg else ['--no-playlist', '--restrict-filenames', '--paths', str(output)]
        cmd += ['--extract-audio', '--audio-format', 'mp3'] if mode == 'Áudio MP3' else ['--format', 'bv*+ba/b', '--merge-output-format', 'mp4']
        return cmd + [url]
    if kind == 'Arquivo':
        file = Path(source)
        if not file.is_file():
            raise ValueError('Selecione um arquivo de vídeo existente.')
        if not ffmpeg:
            raise ValueError('FFmpeg não encontrado. Veja o README.')
        target = output / (file.stem + ('.mp3' if mode == 'Áudio MP3' else '.mp4'))
        if target.exists():
            raise ValueError('O arquivo de saída já existe. Renomeie ou remova antes de continuar.')
        return [ffmpeg, '-nostdin', '-i', str(file), '-vn', '-codec:a', 'libmp3lame', '-q:a', '2', str(target)] if mode == 'Áudio MP3' else [ffmpeg, '-nostdin', '-i', str(file), '-c:v', 'libx264', '-c:a', 'aac', str(target)]
    drive = source.strip().upper().rstrip('\\/:')
    if len(drive) != 1 or not drive.isalpha():
        raise ValueError('Informe a letra da unidade, por exemplo D.')
    if kind == 'DVD / Blu-ray':
        mkv = executable('makemkvcon')
        if not mkv:
            raise ValueError('Instale o MakeMKV e adicione makemkvcon.exe ao PATH.')
        # MakeMKV accepts a Windows drive path as a disc input.
        return [mkv, 'mkv', f'dev:{drive}:\\', 'all', str(output)]
    ripper = executable('cdparanoia') or executable('cdda2wav')
    if not ripper:
        raise ValueError('Instale cdda2wav para Windows e adicione ao PATH para extrair CD de áudio.')
    if Path(ripper).stem.lower() == 'cdda2wav':
        return [ripper, f'device={drive}:', '-B', '-Owav', 'track']
    raise ValueError('Use cdda2wav para CD no Windows.')


class App:
    def __init__(self, root):
        self.root = root
        root.title('Extrator de Mídia')
        root.geometry('760x570')
        root.minsize(650, 510)
        root.configure(bg='#101827')
        self.events = queue.Queue()
        self.process = None
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', padding=8)
        box = tk.Frame(root, bg='#101827', padx=28, pady=22)
        box.pack(fill='both', expand=True)
        tk.Label(box, text='EXTRATOR DE MÍDIA', bg='#101827', fg='#69dbca', font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        tk.Label(box, text='Vídeos, música e seus discos em um só lugar', bg='#101827', fg='white', font=('Segoe UI', 19, 'bold')).pack(anchor='w', pady=(4, 20))
        self.kind = tk.StringVar(value='Link')
        self.mode = tk.StringVar(value='Áudio MP3')
        self.source = tk.StringVar()
        self.output = tk.StringVar(value=str(Path.home() / 'Downloads'))
        self.field(box, 'ORIGEM', self.kind, ('Link', 'Arquivo', 'CD de áudio', 'DVD / Blu-ray'))
        self.source_label = tk.Label(box, text='LINK HTTPS, ARQUIVO OU LETRA DA UNIDADE', bg='#101827', fg='#aabbcf', font=('Segoe UI', 10, 'bold'))
        self.source_label.pack(anchor='w', pady=(17, 5))
        row = tk.Frame(box, bg='#101827'); row.pack(fill='x')
        tk.Entry(row, textvariable=self.source, font=('Segoe UI', 11), bg='#e7eef7', relief='flat').pack(side='left', fill='x', expand=True, ipady=10)
        tk.Button(row, text='Procurar', command=self.browse, bg='#344760', fg='white', relief='flat', padx=12).pack(side='left', padx=(8, 0), ipady=8)
        self.field(box, 'FORMATO (DISCOS: CÓPIA NO FORMATO ORIGINAL)', self.mode, ('Áudio MP3', 'Vídeo MP4'))
        tk.Label(box, text='SALVAR EM', bg='#101827', fg='#aabbcf', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(17, 5))
        row = tk.Frame(box, bg='#101827'); row.pack(fill='x')
        tk.Entry(row, textvariable=self.output, font=('Segoe UI', 11), bg='#e7eef7', relief='flat').pack(side='left', fill='x', expand=True, ipady=10)
        tk.Button(row, text='Pasta', command=self.folder, bg='#344760', fg='white', relief='flat', padx=19).pack(side='left', padx=(8, 0), ipady=8)
        row = tk.Frame(box, bg='#101827'); row.pack(fill='x', pady=20)
        self.start = tk.Button(row, text='INICIAR EXTRAÇÃO', command=self.run, bg='#34bfae', fg='#081c26', font=('Segoe UI', 11, 'bold'), relief='flat', padx=20, pady=10)
        self.start.pack(side='left')
        tk.Button(row, text='Cancelar', command=self.cancel, bg='#344760', fg='white', relief='flat', padx=15, pady=10).pack(side='left', padx=10)
        self.log = tk.Text(box, bg='#182538', fg='#d8e6f3', font=('Consolas', 9), relief='flat', height=9, state='disabled')
        self.log.pack(fill='both', expand=True)
        self.kind.trace_add('write', self.update_kind)
        root.after(100, self.poll)

    def field(self, parent, label, value, choices):
        tk.Label(parent, text=label, bg='#101827', fg='#aabbcf', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 5))
        ttk.Combobox(parent, textvariable=value, values=choices, state='readonly', font=('Segoe UI', 11)).pack(fill='x')

    def update_kind(self, *_):
        self.source_label.config(text='LETRA DA UNIDADE (EX.: D)' if self.kind.get() in ('CD de áudio', 'DVD / Blu-ray') else 'LINK HTTPS OU CAMINHO DO ARQUIVO')
        if self.kind.get() == 'CD de áudio': self.mode.set('Áudio MP3')

    def browse(self):
        filename = filedialog.askopenfilename(title='Selecione seu vídeo')
        if filename: self.kind.set('Arquivo'); self.source.set(filename)

    def folder(self):
        folder = filedialog.askdirectory()
        if folder: self.output.set(folder)

    def write(self, line):
        self.log.config(state='normal'); self.log.insert('end', line + '\n'); self.log.see('end'); self.log.config(state='disabled')

    def run(self):
        if self.process: return
        try:
            output = Path(self.output.get()).expanduser()
            if not output.is_dir(): raise ValueError('Selecione uma pasta de destino existente.')
            kind = self.kind.get()
            if kind == 'CD de áudio' and self.mode.get() != 'Áudio MP3': raise ValueError('CD de áudio só contém áudio.')
            cmd = command_for(kind, self.source.get(), output, self.mode.get())
        except ValueError as exc:
            messagebox.showerror('Verifique os dados', str(exc)); return
        self.start.config(state='disabled')
        self.write('Iniciando: ' + kind)
        threading.Thread(target=self.worker, args=(cmd, output, kind), daemon=True).start()

    def worker(self, cmd, output, kind):
        try:
            before = set(output.glob('*.wav')) if kind == 'CD de áudio' else set()
            self.process = subprocess.Popen(cmd, cwd=str(output) if kind == 'CD de áudio' else None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors='replace', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            for line in self.process.stdout:
                self.events.put(('log', line.rstrip()))
            code = self.process.wait()
            if code == 0 and kind == 'CD de áudio':
                ffmpeg = executable('ffmpeg')
                if not ffmpeg:
                    self.events.put(('log', 'Faixas WAV salvas. Instale FFmpeg para conversão automática em MP3.'))
                else:
                    for wav in sorted(set(output.glob('*.wav')) - before):
                        mp3 = wav.with_suffix('.mp3')
                        if mp3.exists():
                            self.events.put(('log', f'{mp3.name} já existe; conversão ignorada.'))
                            continue
                        result = subprocess.run([ffmpeg, '-nostdin', '-i', str(wav), '-codec:a', 'libmp3lame', '-q:a', '2', str(mp3)], capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                        if result.returncode: code = result.returncode; self.events.put(('log', f'Falha ao converter {wav.name}.'))
            self.events.put(('done', code, output, kind))
        except Exception as exc:
            self.events.put(('error', str(exc)))
        finally:
            self.process = None

    def cancel(self):
        if self.process: self.process.terminate(); self.write('Cancelamento solicitado.')

    def poll(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == 'log': self.write(event[1])
                elif event[0] == 'error':
                    self.start.config(state='normal'); messagebox.showerror('Erro', event[1])
                else:
                    _, code, output, kind = event
                    self.start.config(state='normal')
                    if code == 0:
                        self.write('Concluído. Arquivos em: ' + str(output))
                        messagebox.showinfo('Concluído', 'Extração finalizada.\n' + str(output))
                    else: self.write(f'Falha na extração (código {code}). Confira o registro acima.')
        except queue.Empty: pass
        self.root.after(100, self.poll)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--yt-dlp':
        sys.argv.pop(1)
        from yt_dlp import main
        main()
    else:
        root = tk.Tk(); App(root); root.mainloop()
