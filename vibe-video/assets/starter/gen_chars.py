# collects every CJK char used anywhere in src/ so the font preloader can fetch all needed subsets
import glob
src=''.join(open(f, encoding='utf-8').read() for f in glob.glob('src/**/*.ts*', recursive=True) if not f.endswith('allchars.ts'))
chars=sorted(set(c for c in src if ord(c)>0x2000 and c!='龥'))
open('src/allchars.ts','w', encoding='utf-8').write('export const ALL_CHARS = %r;\n' % ''.join(chars))
print(len(chars))
