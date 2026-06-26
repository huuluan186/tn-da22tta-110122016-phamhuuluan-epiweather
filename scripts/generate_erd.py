"""
Sinh ERD diagram cho kltn_epiweather bằng Graphviz.
FK lấy từ dump thật (kltn_schema.sql) — đúng 17 quan hệ.
Output: docs/diagrams/erd_kltn.svg  (vector, nét ở mọi kích cỡ)
        docs/diagrams/erd_kltn.png  (600 dpi, dự phòng)

Cài: pip install graphviz
Cần: Graphviz binary  https://graphviz.org/download/
     Trên Windows: winget install Graphviz.Graphviz
"""
from graphviz import Digraph
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'docs' / 'diagrams' / 'erd_kltn'

# ── Màu style pgAdmin (đồng nhất, không theo tầng) ────────────────────────────
HDR_COLOR = '#6C9AC3'   # header xanh nhạt như pgAdmin
BG_COLOR  = '#FFFFFF'   # body trắng
BG_VIEW   = '#F5F5F5'   # view hơi xám phân biệt
BG  = {0: BG_COLOR, 1: BG_COLOR, 2: BG_COLOR,
       3: BG_COLOR, 4: BG_COLOR, 5: BG_VIEW}
HDR = {0: HDR_COLOR, 1: HDR_COLOR, 2: HDR_COLOR,
       3: HDR_COLOR, 4: HDR_COLOR, 5: '#888888'}

# ── Định nghĩa bảng: (tên_cột, kiểu, 'PK'/'FK'/'') ──────────────────────────
TABLES = {
    # Tầng 0
    'countries': (0, [
        ('iso3',           'char(3)',     'PK'),
        ('iso2',           'char(2)',     ''),
        ('country_name',   'varchar(100)',''),
        ('who_region',     'varchar(10)', ''),
        ('who_region_enc', 'smallint',    ''),
        ('latitude',       'float',       ''),
        ('longitude',      'float',       ''),
        ('population',     'bigint',      ''),
        ('created_at',     'timestamptz', ''),
    ]),
    # Tầng 1
    'diseases': (1, [
        ('id',               'integer',     'PK'),
        ('code',             'varchar(20)', ''),
        ('display_name',     'varchar(100)',''),
        ('target_variable',  'varchar(50)', ''),
        ('target_transform', 'varchar(20)', ''),
        ('is_active',        'boolean',     ''),
        ('created_at',       'timestamptz', ''),
    ]),
    'data_sources': (1, [
        ('id',               'integer',     'PK'),
        ('code',             'varchar(30)', ''),
        ('source_type',      'varchar(20)', ''),
        ('url',              'text',        ''),
        ('update_frequency', 'varchar(20)', ''),
        ('spatial_coverage', 'varchar(50)', ''),
        ('temporal_start',   'date',        ''),
        ('is_active',        'boolean',     ''),
    ]),
    'weather_variables': (1, [
        ('id',            'integer',     'PK'),
        ('code',          'varchar(50)', ''),
        ('display_name',  'varchar(100)',''),
        ('unit',          'varchar(20)', ''),
        ('source_id',     'integer',     'FK'),
        ('era5_variable', 'varchar(100)',''),
        ('is_active',     'boolean',     ''),
    ]),
    # Tầng 2
    'disease_cases': (2, [
        ('id',                'bigint',   'PK'),
        ('disease_id',        'integer',  'FK'),
        ('iso3',              'char(3)',   'FK'),
        ('source_id',         'integer',  'FK'),
        ('iso_year',          'smallint', ''),
        ('iso_week',          'smallint', ''),
        ('raw_count',         'integer',  ''),
        ('transformed_value', 'float',    ''),
        ('data_quality',      'smallint', ''),
        ('ingested_at',       'timestamptz',''),
    ]),
    'weather_observations': (2, [
        ('id',          'bigint',    'PK'),
        ('iso3',        'char(3)',   'FK'),
        ('source_id',   'integer',  'FK'),
        ('iso_year',    'smallint', ''),
        ('iso_week',    'smallint', ''),
        ('data',        'jsonb',    ''),
        ('ingested_at', 'timestamptz',''),
    ]),
    # Tầng 3
    'feature_configs': (3, [
        ('id',              'integer',     'PK'),
        ('disease_id',      'integer',     'FK'),
        ('feature_name',    'varchar(100)',''),
        ('source_type',     'varchar(20)', ''),
        ('weather_variable','varchar(50)', ''),
        ('lag_weeks',       'smallint',    ''),
        ('transform',       'varchar(20)', ''),
        ('is_active',       'boolean',     ''),
        ('version_tag',     'varchar(30)', ''),
    ]),
    'feature_snapshots': (3, [
        ('disease_id',      'integer',    'PK/FK'),
        ('iso3',            'char(3)',    'PK/FK'),
        ('iso_year',        'smallint',  'PK'),
        ('iso_week',        'smallint',  'PK'),
        ('feature_version', 'varchar(10)','PK'),
        ('features',        'jsonb',     ''),
        ('created_at',      'timestamptz',''),
        ('updated_at',      'timestamptz',''),
    ]),
    'model_versions': (3, [
        ('id',               'integer',     'PK'),
        ('disease_id',       'integer',     'FK'),
        ('version',          'varchar(30)', ''),
        ('algorithm',        'varchar(30)', ''),
        ('train_year_start', 'smallint',    ''),
        ('train_year_end',   'smallint',    ''),
        ('val_year',         'smallint',    ''),
        ('hyperparams',      'jsonb',       ''),
        ('artifact_path',    'varchar(255)',''),
        ('is_active',        'boolean',     ''),
        ('is_champion',      'boolean',     ''),
        ('created_at',       'timestamptz', ''),
    ]),
    'model_evaluations': (3, [
        ('id',               'integer',    'PK'),
        ('model_version_id', 'integer',    'FK'),
        ('eval_set',         'varchar(30)',''),
        ('eval_type',        'varchar(20)',''),
        ('r2_score',         'float',      ''),
        ('mae',              'float',      ''),
        ('rmse',             'float',      ''),
        ('risk_macro_f1',    'float',      ''),
        ('risk_low_f1',      'float',      ''),
        ('risk_medium_f1',   'float',      ''),
        ('risk_high_f1',     'float',      ''),
        ('n_samples',        'integer',    ''),
        ('evaluated_at',     'timestamptz',''),
    ]),
    'risk_thresholds': (3, [
        ('id',                 'integer',    'PK'),
        ('disease_id',         'integer',    'FK'),
        ('iso3',               'varchar(10)',''),
        ('q33',                'float',      ''),
        ('q67',                'float',      ''),
        ('n_nonzero_weeks',    'integer',    ''),
        ('is_global_fallback', 'boolean',    ''),
        ('model_version_id',   'integer',    'FK'),
        ('updated_at',         'timestamptz',''),
    ]),
    'predictions': (3, [
        ('id',               'bigint',     'PK'),
        ('disease_id',       'integer',    'FK'),
        ('iso3',             'char(3)',    'FK'),
        ('iso_year',         'smallint',  ''),
        ('iso_week',         'smallint',  ''),
        ('horizon_weeks',    'smallint',  ''),
        ('predicted_value',  'float',     ''),
        ('predicted_cases',  'float',     ''),
        ('risk_level',       'varchar(10)',''),
        ('risk_probability', 'float',     ''),
        ('confidence_lo',    'float',     ''),
        ('confidence_hi',    'float',     ''),
        ('model_version_id', 'integer',   'FK'),
        ('created_at',       'timestamptz',''),
    ]),
    # Tầng 4
    'pipeline_runs': (4, [
        ('run_id',           'uuid',       'PK'),
        ('pipeline_name',    'varchar(50)',''),
        ('pipeline_version', 'varchar(20)',''),
        ('trigger_type',     'varchar(20)',''),
        ('status',           'varchar(20)',''),
        ('iso_year',         'smallint',  ''),
        ('iso_week',         'smallint',  ''),
        ('started_at',       'timestamptz',''),
        ('completed_at',     'timestamptz',''),
        ('duration_sec',     'float',     ''),
        ('rows_processed',   'integer',   ''),
        ('errors',           'jsonb',     ''),
    ]),
    'data_quality_checks': (4, [
        ('id',           'integer',     'PK'),
        ('run_id',       'uuid',        'FK'),
        ('check_name',   'varchar(100)',''),
        ('table_name',   'varchar(50)', ''),
        ('iso_year',     'smallint',   ''),
        ('iso_week',     'smallint',   ''),
        ('threshold',    'float',      ''),
        ('actual_value', 'float',      ''),
        ('passed',       'boolean',    ''),
        ('detail',       'text',       ''),
        ('checked_at',   'timestamptz',''),
    ]),
    'api_request_logs': (4, [
        ('id',           'bigint',     'PK'),
        ('endpoint',     'varchar(100)',''),
        ('method',       'varchar(10)', ''),
        ('disease',      'varchar(20)', ''),
        ('iso3',         'char(3)',     ''),
        ('iso_year',     'smallint',   ''),
        ('iso_week',     'smallint',   ''),
        ('response_ms',  'integer',    ''),
        ('status_code',  'smallint',   ''),
        ('requested_at', 'timestamptz',''),
    ]),
    'alembic_version': (4, [
        ('version_num', 'varchar(32)', 'PK'),
    ]),
    # Tầng 5 — View
    'mv_latest_predictions': (5, [
        ('disease_id',      'integer',    ''),
        ('disease_code',    'varchar(20)',''),
        ('iso3',            'char(3)',    ''),
        ('country_name',    'varchar(100)',''),
        ('who_region',      'varchar(10)',''),
        ('iso_year',        'smallint',  ''),
        ('iso_week',        'smallint',  ''),
        ('horizon_weeks',   'smallint',  ''),
        ('predicted_cases', 'float',     ''),
        ('risk_level',      'varchar(10)',''),
        ('created_at',      'timestamptz',''),
    ]),
}

# ── 17 FK thật — lấy từ kltn_schema.sql dump ─────────────────────────────────
# format: (from_table, to_table, label)
FOREIGN_KEYS = [
    ('disease_cases',        'diseases',       'disease_id'),
    ('disease_cases',        'countries',      'iso3'),
    ('disease_cases',        'data_sources',   'source_id'),
    ('weather_observations', 'countries',      'iso3'),
    ('weather_observations', 'data_sources',   'source_id'),
    ('weather_variables',    'data_sources',   'source_id'),
    ('feature_configs',      'diseases',       'disease_id'),
    ('feature_snapshots',    'diseases',       'disease_id'),
    ('feature_snapshots',    'countries',      'iso3'),
    ('model_versions',       'diseases',       'disease_id'),
    ('model_evaluations',    'model_versions', 'model_version_id'),
    ('risk_thresholds',      'diseases',       'disease_id'),
    ('risk_thresholds',      'model_versions', 'model_version_id'),
    ('predictions',          'diseases',       'disease_id'),
    ('predictions',          'countries',      'iso3'),
    ('predictions',          'model_versions', 'model_version_id'),
    ('data_quality_checks',  'pipeline_runs',  'run_id'),
]


def make_label(name, columns, tier):
    bg  = BG[tier]
    hdr = HDR[tier]
    rows = ''
    for col_name, col_type, col_key in columns:
        if   'PK' in col_key and 'FK' in col_key:
            prefix    = 'PK/FK'
            wrap_open = '<B>'
            wrap_close= '</B>'
            color     = f' BGCOLOR="{bg}"'
        elif col_key == 'PK':
            prefix    = 'PK   '
            wrap_open = '<B>'
            wrap_close= '</B>'
            color     = f' BGCOLOR="{bg}"'
        elif col_key == 'FK':
            prefix    = '  FK '
            wrap_open = ''
            wrap_close= ''
            color     = f' BGCOLOR="{bg}"'
        else:
            prefix    = '     '
            wrap_open = ''
            wrap_close= ''
            color     = f' BGCOLOR="{bg}"'

        rows += (
            f'<TR>'
            f'<TD ALIGN="LEFT"{color}>'
            f'<FONT POINT-SIZE="9.5"> {prefix}  {wrap_open}{col_name}{wrap_close} </FONT>'
            f'</TD>'
            f'<TD ALIGN="LEFT"{color}>'
            f'<FONT POINT-SIZE="8.5" COLOR="#555555"> {col_type} </FONT>'
            f'</TD>'
            f'</TR>'
        )

    suffix = ' (view)' if tier == 5 else ''
    label = (
        f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="2">'
        f'<TR><TD ALIGN="CENTER" COLSPAN="2" BGCOLOR="{hdr}">'
        f'<FONT COLOR="white" POINT-SIZE="11"><B> {name}{suffix} </B></FONT>'
        f'</TD></TR>'
        f'{rows}'
        f'</TABLE>>'
    )
    return label


def build_erd():
    dot = Digraph(
        name='kltn_epiweather_erd',
        comment='ERD — kltn_epiweather (16 bảng + 1 view)',
        format='svg',
    )
    dot.attr(
        rankdir='TB',
        splines='ortho',
        nodesep='0.6',
        ranksep='1.0',
        fontname='Arial',
        bgcolor='white',
        pad='0.6',
    )
    dot.attr('node', shape='none', margin='0', fontname='Arial')
    dot.attr('edge', fontsize='8', fontname='Arial',
             arrowhead='normal', arrowsize='0.7', color='#444444')

    CLUSTER_STYLE = dict(style='dashed', color='#AAAAAA',
                         fontcolor='#666666', fontsize='10')

    with dot.subgraph(name='cluster_t0') as s:
        s.attr(label='Tầng 0 — Địa lý', **CLUSTER_STYLE)
        s.node('countries', make_label('countries', TABLES['countries'][1], 0))

    with dot.subgraph(name='cluster_t1') as s:
        s.attr(label='Tầng 1 — Danh mục', rank='same', **CLUSTER_STYLE)
        for t in ('diseases', 'data_sources', 'weather_variables'):
            tier, cols = TABLES[t]
            s.node(t, make_label(t, cols, tier))

    with dot.subgraph(name='cluster_t2') as s:
        s.attr(label='Tầng 2 — Quan sát', rank='same', **CLUSTER_STYLE)
        for t in ('disease_cases', 'weather_observations'):
            tier, cols = TABLES[t]
            s.node(t, make_label(t, cols, tier))

    with dot.subgraph(name='cluster_t3') as s:
        s.attr(label='Tầng 3 — Pipeline ML', **CLUSTER_STYLE)
        for t in ('feature_configs', 'feature_snapshots',
                  'model_versions', 'model_evaluations',
                  'risk_thresholds', 'predictions'):
            tier, cols = TABLES[t]
            s.node(t, make_label(t, cols, tier))

    with dot.subgraph(name='cluster_t4') as s:
        s.attr(label='Tầng 4 — Vận hành', rank='same', **CLUSTER_STYLE)
        for t in ('pipeline_runs', 'data_quality_checks',
                  'api_request_logs', 'alembic_version'):
            tier, cols = TABLES[t]
            s.node(t, make_label(t, cols, tier))

    with dot.subgraph(name='cluster_t5') as s:
        s.attr(label='Materialized View', **CLUSTER_STYLE)
        t = 'mv_latest_predictions'
        tier, cols = TABLES[t]
        s.node(t, make_label(t, cols, tier))

    # ── 17 FK edges ───────────────────────────────────────────────────────────
    # splines=ortho không hỗ trợ edge label — dùng xlabel thay thế
    for frm, to, lbl in FOREIGN_KEYS:
        dot.edge(frm, to, xlabel=f' {lbl} ', color='#3A6EA5',
                 fontcolor='#777777', style='solid')

    return dot


if __name__ == '__main__':
    dot = build_erd()

    # SVG (vector — dùng cho báo cáo)
    svg_path = dot.render(str(OUTPUT), format='svg', cleanup=True)
    print(f'SVG: {svg_path}')

    # PNG 300 dpi dự phòng (cần Graphviz >= 2.40)
    try:
        import subprocess, shutil
        gv_bin = shutil.which('dot')
        if gv_bin:
            src = str(OUTPUT) + '.gv'
            dot.save(src)
            png_path = str(OUTPUT) + '.png'
            subprocess.run(
                [gv_bin, '-Tpng', f'-Gdpi=300', src, '-o', png_path],
                check=True
            )
            Path(src).unlink(missing_ok=True)
            print(f'PNG 300dpi: {png_path}')
    except Exception as e:
        print(f'PNG skipped: {e}')

    print('Xong.')
