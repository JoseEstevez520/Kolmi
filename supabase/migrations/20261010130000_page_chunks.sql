-- Search over pages: chunks with embeddings and full text, and the hybrid search function.
-- Also in schema.sql.

-- The search index over pages: each page cut into chunks, each with its embedding and a
-- full-text vector, so a question finds meaning and exact words alike. Following Supabase's
-- guides: https://supabase.com/docs/guides/ai/semantic-search (pgvector),
-- https://supabase.com/docs/guides/ai/hybrid-search (full text + semantic) and
-- https://supabase.com/docs/guides/ai/vector-indexes/hnsw (the index).
create extension if not exists vector with schema extensions;

create table if not exists page_chunks (
  id bigserial primary key,
  node_id bigint not null references nodes(id) on delete cascade,
  position int not null,
  heading text not null default '',
  content text not null,
  -- sha256 of the page's whole content_md, the same on all its chunks: how the index knows a
  -- page changed.
  content_hash text not null,
  embedding extensions.vector(1536) not null,
  fts tsvector generated always as (to_tsvector('simple', heading || ' ' || content)) stored,
  created_at timestamptz not null default now()
);

create index if not exists page_chunks_node_id_idx on page_chunks (node_id);
create index if not exists page_chunks_embedding_idx
  on page_chunks using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists page_chunks_fts_idx on page_chunks using gin (fts);

-- Hybrid search with Reciprocal Rank Fusion, from
-- https://supabase.com/docs/guides/ai/hybrid-search: the best chunks by full text and by
-- cosine distance, each ranked, then fused as the sum of weight / (rrf_k + rank).
create or replace function match_page_chunks(
  query_text text,
  query_embedding extensions.vector(1536),
  match_count int default 8,
  full_text_weight float default 1,
  semantic_weight float default 1,
  rrf_k int default 50
)
returns table (id bigint, node_id bigint, heading text, content text, score float)
language sql
set search_path = public, extensions
as $$
  with full_text as (
    select
      c.id,
      row_number() over (
        order by ts_rank_cd(c.fts, websearch_to_tsquery('simple', query_text)) desc
      ) as rank_ix
    from page_chunks c
    where c.fts @@ websearch_to_tsquery('simple', query_text)
    order by rank_ix
    limit least(match_count, 30) * 2
  ),
  semantic as (
    select
      c.id,
      row_number() over (order by c.embedding <=> query_embedding) as rank_ix
    from page_chunks c
    order by rank_ix
    limit least(match_count, 30) * 2
  )
  select
    pc.id,
    pc.node_id,
    pc.heading,
    pc.content,
    (
      coalesce(full_text_weight / (rrf_k + full_text.rank_ix), 0.0) +
      coalesce(semantic_weight / (rrf_k + semantic.rank_ix), 0.0)
    )::float as score
  from full_text
  full outer join semantic on full_text.id = semantic.id
  join page_chunks pc on pc.id = coalesce(full_text.id, semantic.id)
  order by score desc
  limit least(match_count, 30);
$$;

-- RLS on, with no public policies, as every table but settings: only the backend (service
-- role) gets in.
alter table page_chunks enable row level security;
