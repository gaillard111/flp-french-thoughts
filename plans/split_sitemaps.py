#!/usr/bin/env python3
"""
FLP Sitemap Splitter
====================
Splits large sitemap1.xml (50k URLs) and sitemap2.xml (48k URLs)
into smaller sitemaps of max 12,500 URLs each, so Google can read them.

Usage: python3 split_sitemaps.py [--dry-run]

Steps:
1. Create backup of sitemaps directory
2. Parse sitemap1.xml and sitemap2.xml, collect all <url> blocks
3. Split into chunks of max 12,500 URLs
4. Write sitemap_1.xml .. sitemap_N.xml
5. Update sitemap.xml index to reference new files + sitemap_static.xml
6. Move old sitemap1.xml, sitemap2.xml to backup/
"""

import os
import sys
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

SITEMAPS_DIR = "/home/flp/app/web/sitemaps"
BACKUP_DIR = os.path.join(SITEMAPS_DIR, "backup")
MAX_URLS = 12500
SITE_BASE = "https://filsdelapensee.ch"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

# Register namespace so ElementTree output has correct prefixes
ET.register_namespace("", SITEMAP_NS)

DRY_RUN = "--dry-run" in sys.argv

def log(msg):
    prefix = "[DRY-RUN] " if DRY_RUN else ""
    print(f"{prefix}{msg}")

def step(msg):
    log(f"\n{'='*60}")
    log(f"  {msg}")
    log(f"{'='*60}")

def backup_directory():
    """Step 1: Create a backup of the sitemaps directory."""
    step("1. Creating backup of sitemaps directory")
    
    if not os.path.isdir(SITEMAPS_DIR):
        print(f"ERROR: {SITEMAPS_DIR} does not exist!")
        sys.exit(1)
    
    if not DRY_RUN:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        for fname in ["sitemap1.xml", "sitemap2.xml", "sitemap.xml", "sitemap_static.xml"]:
            src = os.path.join(SITEMAPS_DIR, fname)
            dst = os.path.join(BACKUP_DIR, fname)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                log(f"  Copied {fname} -> backup/")
    else:
        log("  Would copy all sitemap files to backup/")

def extract_urls_from_sitemap(filepath):
    """Extract all <url> elements from a sitemap XML file."""
    log(f"  Reading {filepath}...")
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    urls = []
    for url_elem in root.findall(f"{{{SITEMAP_NS}}}url"):
        urls.append(url_elem)
    
    log(f"  Found {len(urls)} URLs")
    return urls

def parse_sitemaps():
    """Step 2: Read both sitemaps and collect all <url> elements."""
    step("2. Reading sitemap1.xml and sitemap2.xml")
    
    sitemap1_path = os.path.join(SITEMAPS_DIR, "sitemap1.xml")
    sitemap2_path = os.path.join(SITEMAPS_DIR, "sitemap2.xml")
    
    if not os.path.exists(sitemap1_path):
        print(f"ERROR: {sitemap1_path} not found!")
        sys.exit(1)
    if not os.path.exists(sitemap2_path):
        print(f"ERROR: {sitemap2_path} not found!")
        sys.exit(1)
    
    all_urls = []
    all_urls.extend(extract_urls_from_sitemap(sitemap1_path))
    all_urls.extend(extract_urls_from_sitemap(sitemap2_path))
    
    log(f"\n  Total URLs collected: {len(all_urls)}")
    return all_urls

def split_and_write_sitemaps(all_urls):
    """Step 3 & 4: Split URLs into chunks and write new sitemap files."""
    step(f"3/4. Splitting URLs (max {MAX_URLS} per file) and writing new sitemaps")
    
    total = len(all_urls)
    num_files = (total + MAX_URLS - 1) // MAX_URLS  # ceiling division
    log(f"  Will create {num_files} sitemap files")
    
    today = datetime.now().strftime("%Y-%m-%d")
    created_files = []
    
    for i in range(num_files):
        start = i * MAX_URLS
        end = min(start + MAX_URLS, total)
        chunk = all_urls[start:end]
        
        fname = f"sitemap_{i+1}.xml"
        fpath = os.path.join(SITEMAPS_DIR, fname)
        created_files.append((fname, len(chunk)))
        
        log(f"\n  Creating {fname} ({len(chunk)} URLs)...")
        
        if not DRY_RUN:
            # Build XML manually to preserve structure cleanly
            lines = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                f'<urlset xmlns="{SITEMAP_NS}">'
            ]
            
            for url_elem in chunk:
                loc = url_elem.find(f"{{{SITEMAP_NS}}}loc").text
                lastmod_elem = url_elem.find(f"{{{SITEMAP_NS}}}lastmod")
                changefreq_elem = url_elem.find(f"{{{SITEMAP_NS}}}changefreq")
                priority_elem = url_elem.find(f"{{{SITEMAP_NS}}}priority")
                
                lines.append("  <url>")
                lines.append(f"    <loc>{loc}</loc>")
                if lastmod_elem is not None:
                    lines.append(f"    <lastmod>{lastmod_elem.text}</lastmod>")
                if changefreq_elem is not None:
                    lines.append(f"    <changefreq>{changefreq_elem.text}</changefreq>")
                if priority_elem is not None:
                    lines.append(f"    <priority>{priority_elem.text}</priority>")
                lines.append("  </url>")
            
            lines.append("</urlset>")
            
            with open(fpath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            
            # Verify file was written
            size = os.path.getsize(fpath)
            log(f"    Written: {size:,} bytes")
        else:
            log(f"    Would write {fname} with {len(chunk)} URLs")
    
    return created_files

def update_sitemap_index(created_files):
    """Step 5: Update sitemap.xml to reference new files + sitemap_static.xml."""
    step("5. Updating sitemap.xml index")
    
    index_path = os.path.join(SITEMAPS_DIR, "sitemap.xml")
    today = datetime.now().strftime("%Y-%m-%d")
    
    log(f"  Writing new sitemap.xml index...")
    
    if not DRY_RUN:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<sitemapindex xmlns="{SITEMAP_NS}">',
            '  <sitemap>',
            f'    <loc>{SITE_BASE}/sitemaps/sitemap_static.xml</loc>',
            f'    <lastmod>{today}</lastmod>',
            '  </sitemap>',
        ]
        
        for fname, count in created_files:
            lines.extend([
                '  <sitemap>',
                f'    <loc>{SITE_BASE}/sitemaps/{fname}</loc>',
                f'    <lastmod>{today}</lastmod>',
                '  </sitemap>',
            ])
        
        lines.append('</sitemapindex>')
        
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        
        log(f"  Written sitemap.xml with {len(created_files) + 1} sitemap entries")
    else:
        log(f"  Would write sitemap.xml with {len(created_files) + 1} entries:")
        log(f"    - sitemap_static.xml")
        for fname, count in created_files:
            log(f"    - {fname} ({count} URLs)")

def cleanup_old_sitemaps():
    """Step 6: Move old sitemap1.xml and sitemap2.xml to backup."""
    step("6. Moving old sitemap1.xml and sitemap2.xml to backup/")
    
    for fname in ["sitemap1.xml", "sitemap2.xml"]:
        src = os.path.join(SITEMAPS_DIR, fname)
        dst = os.path.join(BACKUP_DIR, fname)
        
        if os.path.exists(src):
            if not DRY_RUN:
                # Move to backup directory
                os.makedirs(BACKUP_DIR, exist_ok=True)
                shutil.move(src, dst)
                log(f"  Moved {fname} -> backup/{fname}")
            else:
                log(f"  Would move {fname} -> backup/{fname}")
        else:
            log(f"  {fname} already moved/not found, skipping")

def verify_files(created_files):
    """Step 7: Verify new files are in place and readable."""
    step("7. Verifying new sitemap structure")
    
    log(f"\n  Contents of {SITEMAPS_DIR}:")
    log(f"  {'-'*50}")
    
    try:
        for fname in sorted(os.listdir(SITEMAPS_DIR)):
            fpath = os.path.join(SITEMAPS_DIR, fname)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                log(f"  {fname:30s} {size:>10,} bytes")
    except Exception as e:
        log(f"  Error listing directory: {e}")
    
    # Verify each new sitemap is valid XML
    log(f"\n  Validating new sitemap XML files...")
    for fname, expected_count in created_files:
        fpath = os.path.join(SITEMAPS_DIR, fname)
        try:
            tree = ET.parse(fpath)
            root = tree.getroot()
            actual_count = len(root.findall(f"{{{SITEMAP_NS}}}url"))
            if actual_count == expected_count:
                log(f"  ✓ {fname}: {actual_count} URLs (valid)")
            else:
                log(f"  ✗ {fname}: expected {expected_count}, got {actual_count} URLs (MISMATCH!)")
        except Exception as e:
            log(f"  ✗ {fname}: INVALID XML - {e}")
    
    # Verify sitemap.xml index
    index_path = os.path.join(SITEMAPS_DIR, "sitemap.xml")
    try:
        tree = ET.parse(index_path)
        root = tree.getroot()
        sitemap_count = len(root.findall(f"{{{SITEMAP_NS}}}sitemap"))
        log(f"\n  ✓ sitemap.xml: {sitemap_count} sitemap references (valid)")
    except Exception as e:
        log(f"  ✗ sitemap.xml: INVALID - {e}")
    
    log(f"\n  Backup directory: {BACKUP_DIR}")
    log(f"  {'-'*50}")
    try:
        for fname in sorted(os.listdir(BACKUP_DIR)):
            fpath = os.path.join(BACKUP_DIR, fname)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                log(f"  {fname:30s} {size:>10,} bytes")
    except Exception as e:
        log(f"  (backup directory not yet created)")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   FLP Sitemap Splitter                                     ║")
    print("║   Splitting large sitemaps into max 12,500 URLs each       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    if DRY_RUN:
        print("  *** DRY RUN MODE - No files will be modified ***\n")
    
    # Step 1: Backup
    backup_directory()
    
    # Step 2: Parse
    all_urls = parse_sitemaps()
    
    # Step 3 & 4: Split and write
    created_files = split_and_write_sitemaps(all_urls)
    
    # Step 5: Update index
    update_sitemap_index(created_files)
    
    # Step 6: Cleanup
    cleanup_old_sitemaps()
    
    # Step 7: Verify
    verify_files(created_files)
    
    # Summary
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   SUMMARY                                                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    total_urls = len(all_urls)
    total_new_files = len(created_files)
    
    print(f"  Total URLs processed: {total_urls:,}")
    print(f"  New sitemaps created: {total_new_files}")
    print(f"  Max URLs per file:    {MAX_URLS:,}")
    print()
    print(f"  New files:")
    for fname, count in created_files:
        print(f"    {fname:20s} {count:>6,} URLs")
    print()
    print(f"  Index: sitemap.xml ({total_new_files + 1} entries)")
    print()
    
    if DRY_RUN:
        print("  *** DRY RUN - No changes were made ***")
    else:
        print("  ✅ Structure is ready!")
        print("  Next step: Resubmit sitemaps/sitemap.xml to Google Search Console")
    print()


if __name__ == "__main__":
    main()
