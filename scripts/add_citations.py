#!/usr/bin/env python3
"""
Add formatted citations to reading list entries.
Generates APA, Chicago, and BibTeX formats.
"""

import json


def generate_apa_citation(article):
    """Generate APA 7th edition citation."""
    authors = article['authors']
    year = article['year']
    title = article['title']
    
    # Handle citations field
    if isinstance(article.get('citations'), int):
        # Don't include citation count in formal citation
        pass
    
    # For journal articles (simplified - would need more metadata for full APA)
    apa = f"{authors} ({year}). {title}."
    
    return apa


def generate_chicago_citation(article):
    """Generate Chicago style citation."""
    authors = article['authors']
    year = article['year']
    title = article['title']
    
    chicago = f"{authors}. \"{title}.\" {year}."
    
    return chicago


def generate_bibtex_citation(article):
    """Generate BibTeX entry."""
    # Create citation key from first author last name and year
    first_author = article['authors'].split(',')[0].split()[-1] if ',' in article['authors'] else article['authors'].split()[0]
    year = article['year']
    key = f"{first_author.lower().replace(' ', '')}{year}"
    
    title = article['title']
    authors = article['authors']
    url = article['url']
    
    bibtex = f"""@article{{{key},
  author = {{{authors}}},
  title = {{{title}}},
  year = {{{year}}},
  url = {{{url}}}
}}"""
    
    return bibtex


def generate_markdown_citation(article):
    """Generate Markdown citation with link."""
    authors = article['authors']
    year = article['year']
    title = article['title']
    url = article['url']
    
    markdown = f"**{authors}** ({year}). [{title}]({url})."
    
    return markdown


def add_citations_to_all():
    """Add citation formats to all entries in reading list."""
    with open('reading_list.json', 'r') as f:
        data = json.load(f)
    
    print("Adding citation formats to all entries...\n")
    
    for article in data['reading_list']:
        # Add citations field if it doesn't exist
        if 'citations_formatted' not in article:
            article['citations_formatted'] = {}
        
        # Generate all formats
        article['citations_formatted']['apa'] = generate_apa_citation(article)
        article['citations_formatted']['chicago'] = generate_chicago_citation(article)
        article['citations_formatted']['bibtex'] = generate_bibtex_citation(article)
        article['citations_formatted']['markdown'] = generate_markdown_citation(article)
        
        print(f"✓ Added citations for: {article['title'][:50]}...")
    
    # Save updated list
    with open('reading_list.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Added citation formats to {len(data['reading_list'])} entries")
    print("Formats: APA, Chicago, BibTeX, Markdown")


def export_citations(format_type='apa'):
    """Export all citations in specified format."""
    with open('reading_list.json', 'r') as f:
        data = json.load(f)
    
    output_file = f'reading_list_citations_{format_type}.txt'
    
    with open(output_file, 'w') as f:
        if format_type == 'bibtex':
            # BibTeX entries separated by blank lines
            for article in data['reading_list']:
                f.write(article['citations_formatted'][format_type] + '\n\n')
        else:
            # Numbered list for other formats
            for i, article in enumerate(data['reading_list'], 1):
                f.write(f"{i}. {article['citations_formatted'][format_type]}\n\n")
    
    print(f"Exported {format_type.upper()} citations to {output_file}")


def main():
    """Main function."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'export':
        format_type = sys.argv[2] if len(sys.argv) > 2 else 'apa'
        export_citations(format_type)
    else:
        add_citations_to_all()
        
        print("\n" + "="*70)
        print("EXAMPLE CITATIONS")
        print("="*70)
        
        # Show example of first entry
        with open('reading_list.json', 'r') as f:
            data = json.load(f)
        
        if data['reading_list']:
            article = data['reading_list'][0]
            print(f"\nArticle: {article['title'][:60]}...\n")
            print("APA:")
            print(article['citations_formatted']['apa'])
            print("\nChicago:")
            print(article['citations_formatted']['chicago'])
            print("\nMarkdown:")
            print(article['citations_formatted']['markdown'])
            print("\nBibTeX:")
            print(article['citations_formatted']['bibtex'])
        
        print("\n" + "="*70)
        print("To export all citations in a specific format:")
        print("  python scripts/add_citations.py export apa")
        print("  python scripts/add_citations.py export chicago")
        print("  python scripts/add_citations.py export bibtex")
        print("  python scripts/add_citations.py export markdown")


if __name__ == '__main__':
    main()
