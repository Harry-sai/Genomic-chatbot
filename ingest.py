import json, sqlite3

conn = sqlite3.connect("Genomic_chatbot/data/genome.db")
cur = conn.cursor()

with open("Genomic_chatbot/data/H14CORE_annotation.jsonl") as f:
    for line in f:
        r = json.loads(line)

        # motifs
        cur.execute("""
        INSERT OR REPLACE INTO motifs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r["name"],
            r["tf"],
            r["collection"],
            r["datatype"],
            r["quality"],
            r["length"],
            r["consensus"],
            r["gc_content"],
            r["information_content_total"],
            r["information_content_per_base"],
            r["num_words"],
            r["original_motif"]["orientation"],
            r["subtype_order"]
        ))

        # TF metadata
        m = r["masterlist_info"]
        cur.execute("""
        INSERT OR REPLACE INTO tf_metadata VALUES (?,?,?,?,?,?,?)
        """, (
            r["tf"],
            m.get("tfclass_id"),
            m.get("tfclass_superclass"),
            m.get("tfclass_class"),
            m.get("tfclass_family"),
            m.get("tfclass_subfamily"),
            m.get("greco_db_tf")
        ))

        # Gene info (per species)
        for sp, g in m["species"].items():
            cur.execute("""
            INSERT OR REPLACE INTO gene_info VALUES (?,?,?,?,?,?,?,?)
            """, (
                r["tf"],
                sp,
                g.get("gene_symbol"),
                g.get("uniprot_id"),
                g.get("uniprot_ac"),
                g.get("protein_name"),
                ",".join(g.get("hgnc", [])),
                ",".join(g.get("entrez", []))
            ))

        # matrices
        for mt in ["pcm", "pwm", "pfm"]:
            cur.execute("""
            INSERT OR REPLACE INTO matrices VALUES (?,?,?)
            """, (
                r["name"],
                mt.upper(),
                json.dumps(r[mt])
            ))

        # metrics
        for assay, blocks in r["metrics_summary"].items():
            for context, data in blocks.items():
                cur.execute("""
                INSERT OR REPLACE INTO metrics VALUES (?,?,?,?)
                """, (
                    r["name"],
                    assay,
                    context,
                    json.dumps(data)
                ))

        # thresholds
        cur.execute("""
        INSERT OR REPLACE INTO thresholds VALUES (?,?)
        """, (
            r["name"],
            json.dumps(r["standard_thresholds"])
        ))

        # original motif
        om = r["original_motif"]
        cur.execute("""
        INSERT OR REPLACE INTO original_motif VALUES (?,?,?,?,?,?)
        """, (
            r["name"],
            om.get("origin"),
            om.get("name"),
            om.get("motif_datatype"),
            json.dumps(om["subtype_info"]["species_counts"]),
            json.dumps(om["subtype_info"]["datatype_counts"])
        ))

conn.commit()
conn.close()
