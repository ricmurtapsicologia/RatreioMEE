from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')
original = s

qmatch = re.search(r'(\s*const questions = \[.*?\n\s*\];)', s, re.S)
assert qmatch, 'questions array not found'
questions_before = qmatch.group(1)
assert len(re.findall(r'\{\s*id:\s*\d+', questions_before)) == 124, 'expected 124 items'

script_end = s.find('\n</script>', qmatch.end())
assert script_end > qmatch.end(), 'module script end not found'
legacy_runtime = s[qmatch.end():script_end].strip()
Path('contracts').mkdir(exist_ok=True)
Path('contracts/legacy-scoring-quarantine-v1.txt').write_text(
    'QUARANTINED LEGACY PATIENT SCORING — NOT VALIDATED / NOT EXECUTABLE / DO NOT ACTIVATE\n'
    'Captured verbatim from the former patient runtime before source sanitization.\n\n'
    + legacy_runtime + '\n',
    encoding='utf-8',
)

replacements = {
    '<title>SMI 1.1 – Inventário de Modos Esquemáticos</title>': '<title>Como você reage quando algo toca em pontos sensíveis?</title>',
    '<meta name="description" content="Autoavaliação clínica baseada na Terapia dos Esquemas. Identifique seus modos de enfrentamento, visualize os resultados e gere um PDF para acompanhamento terapêutico.">': '<meta name="description" content="Rastreio clínico sobre sentimentos, pensamentos e reações em situações emocionalmente relevantes.">',
    '<meta property="og:title" content="SMI 1.1 – Inventário de Modos Esquemáticos">': '<meta property="og:title" content="Como você reage quando algo toca em pontos sensíveis?">',
    '<meta property="og:description" content="Entenda seus padrões emocionais e modos disfuncionais com base na Terapia dos Esquemas. Resultados destinados à análise clínica pelo psicólogo responsável.">': '<meta property="og:description" content="Rastreio clínico para organizar padrões de reação sem apresentar resultados automáticos ao paciente.">',
    '<meta name="twitter:title" content="SMI 1.1 – Inventário de Modos Esquemáticos">': '<meta name="twitter:title" content="Como você reage quando algo toca em pontos sensíveis?">',
    '<meta name="twitter:description" content="Autoavaliação com base na Terapia dos Esquemas. Gere um relatório visual e compartilhe com seu psicólogo.">': '<meta name="twitter:description" content="Rastreio clínico sobre padrões de reação nos últimos 6 meses.">',
    '<img src="https://i.pinimg.com/736x/58/93/ad/5893ad216808cad704a9071a84e53fe0.jpg" alt="Saúde emocional e modos esquemáticos" class="hero-img" />': '<img src="https://i.pinimg.com/736x/58/93/ad/5893ad216808cad704a9071a84e53fe0.jpg" alt="Imagem de apoio ao rastreio de padrões emocionais" class="hero-img" />',
    '<p> Este formulário ajuda você a refletir sobre sentimentos, pensamentos e reações, baseado na Terapia dos Esquemas (Young), avaliando seus <em>Modos de Enfrentamento Esquemáticos</em>. </p>': '<p>Este rastreio ajuda a organizar como sentimentos, pensamentos e reações aparecem em situações emocionalmente importantes. O conjunto será analisado clinicamente pelo psicólogo responsável.</p>',
}
for old, new in replacements.items():
    if old in s:
        s = s.replace(old, new, 1)

# Keep one governed patient action and remove result/PDF surfaces.
s, n = re.subn(
    r'<div class="actions">.*?</div>\s*</form>',
    '<div class="actions"><button type="submit" id="btn-gerar">Concluir rastreio</button></div>\n\t\t</form>',
    s,
    count=1,
    flags=re.S,
)
assert n == 1, 'actions block not found'
s = re.sub(r'\n\s*<!-- Resultados -->\s*<section id="results".*?</section>', '', s, count=1, flags=re.S)
s = re.sub(r'\n\s*<!-- Biblioteca PDF -->\s*<script src="https://cdnjs\.cloudflare\.com/ajax/libs/jspdf/[^>]+></script>', '', s, count=1)

# Result-only CSS.
s = re.sub(r'\n\s*/\* Results Cards \*/.*?\n\s*/\* Footer \*/', '\n\n\t\t/* Footer */', s, count=1, flags=re.S)
s = re.sub(r'\n\s*/\* Thermometer \*/.*?\n\s*/\* Responsividade \*/', '\n\n\t\t/* Responsividade */', s, count=1, flags=re.S)
s = s.replace('      --pdf:        #d32f2f;\n', '')

# Move the module script back inside body if the legacy markup closed body early.
s = s.replace('\n</body>\n<!-- Módulos JavaScript embutido -->\n<script type="module">', '\n<!-- Módulo de renderização das questões -->\n<script type="module">', 1)

# Replace all scorer/mode interpretation runtime after the exact item bank.
qmatch_now = re.search(r'(\s*const questions = \[.*?\n\s*\];)', s, re.S)
assert qmatch_now and qmatch_now.group(1) == questions_before, 'item bank changed before runtime replacement'
script_end_now = s.find('\n</script>', qmatch_now.end())
assert script_end_now > qmatch_now.end()
render_runtime = r'''

  const $questions = document.getElementById('questions');
  const renderQuestions = () => {
    $questions.innerHTML = questions.map(({ id, text }) => `
      <div class="question" id="q${id}">
        <p style="text-align:justify"><strong>${id}.</strong> ${text}</p>
        <div class="options-inline">
          ${[1,2,3,4,5,6].map(v=>`
            <label><input type="radio" name="q${id}" value="${v}" required> ${v}</label>
          `).join('')}
        </div>
      </div>`
    ).join('');
  };

  document.addEventListener('DOMContentLoaded', () => {
    renderQuestions();
    document.getElementById('darkModeToggle')
      .addEventListener('click', () => document.body.classList.toggle('dark'));
  });'''
s = s[:qmatch_now.end()] + render_runtime + s[script_end_now:]

qmatch_after = re.search(r'(\s*const questions = \[.*?\n\s*\];)', s, re.S)
assert qmatch_after and qmatch_after.group(1) == questions_before, 'clinical items changed during sanitization'

for token in (
    'id="results"',
    'download-pdf',
    'Gerar Resultados',
    'calculateResults',
    'showResults',
    'generatePDF',
    'getSeverity',
    'Modos esquemáticos disfuncionais identificados',
    "getElementById('splash')",
    'jspdf',
):
    assert token not in s, f'legacy patient-result token remains: {token}'

assert 'Concluir rastreio' in s
assert 'últimos 6 meses' in s
assert 'screening-uniformity-v1.js' in s
assert s != original
p.write_text(s, encoding='utf-8')
