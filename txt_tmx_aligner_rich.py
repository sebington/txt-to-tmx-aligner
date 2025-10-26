# /// script
# requires-python = ">=3.11"
# dependencies = ["rich"]
# ///
import re
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import track
from rich.panel import Panel

def clean_line(line):
    """Clean and normalize a line of text."""
    # Remove leading/trailing whitespace
    line = line.strip()
    
    # Remove section numbering at start (e.g., 12.2.3.1, 18.1.1.1)
    line = re.sub(r'^\d+(\.\d+)*\.?\s*', '', line)
    
    return line

def is_valid_segment(text):
    """Check if a text segment should be kept."""
    if not text or len(text.strip()) == 0:
        return False
    
    # Discard single letters
    if len(text.strip()) == 1:
        return False
    
    # Discard lines containing only numbers and basic punctuation
    if re.match(r'^[\d\s\.\-,°%]+$', text.strip()):
        return False
    
    return True

def segment_sentences(text):
    """Split text into sentences while preserving meaningful segments."""
    if not text:
        return []
    
    # Split on sentence boundaries but be careful with abbreviations
    # This regex looks for periods, exclamation marks, or question marks
    # followed by a space and a capital letter, or at end of string
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ü])|(?<=[.!?])$', text)
    
    # Clean and filter sentences
    valid_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if is_valid_segment(sentence):
            valid_sentences.append(sentence)
    
    return valid_sentences

def align_files(source_path, target_path, console):
    """Align source and target files line by line."""
    translation_units = []
    seen_pairs = set()  # Track duplicates
    
    console.print(f"\n[cyan]Lecture des fichiers...[/cyan]")
    
    with open(source_path, 'r', encoding='utf-8') as src_file, \
         open(target_path, 'r', encoding='utf-8') as tgt_file:
        
        source_lines = src_file.readlines()
        target_lines = tgt_file.readlines()
        
        # Ensure files have same number of lines
        max_lines = max(len(source_lines), len(target_lines))
        
        console.print(f"[green]✓[/green] {len(source_lines)} lignes source")
        console.print(f"[green]✓[/green] {len(target_lines)} lignes cible")
        console.print(f"\n[cyan]Alignement en cours...[/cyan]")
        
        for i in track(range(max_lines), description="Traitement", console=console):
            src_line = source_lines[i] if i < len(source_lines) else ""
            tgt_line = target_lines[i] if i < len(target_lines) else ""
            
            # Clean lines
            src_cleaned = clean_line(src_line)
            tgt_cleaned = clean_line(tgt_line)
            
            # Segment into sentences
            src_segments = segment_sentences(src_cleaned) if src_cleaned else [src_cleaned]
            tgt_segments = segment_sentences(tgt_cleaned) if tgt_cleaned else [tgt_cleaned]
            
            # If both lines have content, align them
            if src_cleaned or tgt_cleaned:
                # Handle cases where segmentation produced different numbers of segments
                if len(src_segments) == len(tgt_segments) and len(src_segments) > 0:
                    # Align sentence by sentence
                    for src_seg, tgt_seg in zip(src_segments, tgt_segments):
                        if is_valid_segment(src_seg) and is_valid_segment(tgt_seg):
                            pair_key = (src_seg, tgt_seg)
                            if pair_key not in seen_pairs:
                                translation_units.append({
                                    'source': src_seg,
                                    'target': tgt_seg
                                })
                                seen_pairs.add(pair_key)
                else:
                    # If segmentation doesn't match, treat as whole line
                    if is_valid_segment(src_cleaned) and is_valid_segment(tgt_cleaned):
                        pair_key = (src_cleaned, tgt_cleaned)
                        if pair_key not in seen_pairs:
                            translation_units.append({
                                'source': src_cleaned,
                                'target': tgt_cleaned
                            })
                            seen_pairs.add(pair_key)
    
    return translation_units

def escape_xml(text):
    """Escape special XML characters."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

def export_tmx(translation_units, output_path, source_lang, target_lang, console):
    """Export translation units to TMX format."""
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    tmx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header
    creationtool="Python TXT-TMX Aligner"
    creationtoolversion="1.0"
    datatype="plaintext"
    segtype="sentence"
    adminlang="en"
    srclang="{source_lang}"
    o-tmf="unknown"
    creationdate="{timestamp}">
  </header>
  <body>
'''
    
    for i, unit in enumerate(translation_units, 1):
        tmx_content += f'''    <tu tuid="{i}">
      <tuv xml:lang="{source_lang}">
        <seg>{escape_xml(unit['source'])}</seg>
      </tuv>
      <tuv xml:lang="{target_lang}">
        <seg>{escape_xml(unit['target'])}</seg>
      </tuv>
    </tu>
'''
    
    tmx_content += '''  </body>
</tmx>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(tmx_content)
    
    console.print(f"\n[green]✓ Fichier TMX créé:[/green] [bold]{output_path}[/bold]")
    console.print(f"[green]✓ Unités de traduction:[/green] [bold]{len(translation_units)}[/bold]")

def main():
    console = Console()
    
    # Header
    console.print(Panel.fit(
        "[bold cyan]Alignement TXT → TMX[/bold cyan]\n"
        "Création de mémoires de traduction",
        border_style="cyan"
    ))
    
    # Get source language
    source_lang = Prompt.ask(
        "\n[yellow]Langue source[/yellow]",
        choices=["fr", "en", "es", "de", "it", "pt"],
        default="fr"
    )
    
    # Get target language
    target_lang = Prompt.ask(
        "[yellow]Langue cible[/yellow]",
        choices=["fr", "en", "es", "de", "it", "pt"],
        default="en"
    )
    
    # Get source file
    source_file = Prompt.ask(
        f"\n[yellow]Fichier source ({source_lang})[/yellow]",
        default="source.txt"
    )
    
    # Get target file
    target_file = Prompt.ask(
        f"[yellow]Fichier cible ({target_lang})[/yellow]",
        default="target.txt"
    )
    
    # Get output file
    output_file = Prompt.ask(
        "\n[yellow]Fichier de sortie TMX[/yellow]",
        default="translation_memory.tmx"
    )
    
    # Check if files exist
    if not Path(source_file).exists():
        console.print(f"\n[red]✗ Erreur:[/red] Le fichier [bold]{source_file}[/bold] n'existe pas.")
        return
    
    if not Path(target_file).exists():
        console.print(f"\n[red]✗ Erreur:[/red] Le fichier [bold]{target_file}[/bold] n'existe pas.")
        return
    
    # Summary
    console.print("\n" + "="*60)
    console.print(f"[cyan]Source:[/cyan] {source_file} ({source_lang})")
    console.print(f"[cyan]Cible:[/cyan] {target_file} ({target_lang})")
    console.print(f"[cyan]Sortie:[/cyan] {output_file}")
    console.print("="*60)
    
    # Confirm
    if not Confirm.ask("\n[yellow]Continuer ?[/yellow]", default=True):
        console.print("[red]Opération annulée.[/red]")
        return
    
    try:
        # Align files
        translation_units = align_files(source_file, target_file, console)
        
        # Export to TMX
        export_tmx(translation_units, output_file, source_lang, target_lang, console)
        
        # Display sample
        if translation_units:
            console.print("\n[bold cyan]Aperçu des unités de traduction:[/bold cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column(f"Source ({source_lang})", style="cyan", no_wrap=False)
            table.add_column(f"Cible ({target_lang})", style="green", no_wrap=False)
            
            for unit in translation_units[:5]:
                src_text = unit['source'][:100] + "..." if len(unit['source']) > 100 else unit['source']
                tgt_text = unit['target'][:100] + "..." if len(unit['target']) > 100 else unit['target']
                table.add_row(src_text, tgt_text)
            
            console.print(table)
            
            if len(translation_units) > 5:
                console.print(f"\n[dim]... et {len(translation_units) - 5} autres unités[/dim]")
        
        console.print(f"\n[bold green]✓ Terminé avec succès ![/bold green]")
        
    except Exception as e:
        console.print(f"\n[red]✗ Erreur:[/red] {str(e)}")

if __name__ == "__main__":
    main()
