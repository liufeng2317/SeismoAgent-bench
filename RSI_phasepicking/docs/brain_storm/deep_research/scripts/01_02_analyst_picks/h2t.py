import re,html,sys
t=open(sys.argv[1],encoding='utf-8',errors='ignore').read()
t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S|re.I)
t=re.sub(r'<[^>]+>','\n',t); t=html.unescape(t); t=re.sub(r'\n\s*\n+','\n',t)
print(t)
