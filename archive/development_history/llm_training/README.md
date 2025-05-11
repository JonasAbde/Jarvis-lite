# LLM Træningsforsøg

## Forsøg 1 (11/05/2025)

### Mål
- Finjustere Microsoft's Phi-2 model (2.7B parametre) til dansk
- Implementere dansk svar-generering
- Optimere for CPU-baseret inferens

### Udfordringer mødt
1. GPU hukommelse ikke tilgængelig
2. CPU hukommelse begrænsninger
3. Problemer med 8-bit kvantisering på Windows

### Løsningsforsøg
1. Reducerede model parametre:
   - Mindre batch størrelse (1)
   - Kortere sekvens længde (128 tokens)
   - Gradient accumulation (4 steps)
   
2. CPU optimering:
   - Float32 præcision
   - Low CPU memory usage
   - Deaktiveret CUDA

### Næste skridt
1. Undersøg alternativer:
   - Mindre model (f.eks. GPT-2 small dansk)
   - Cloud-baseret træning
   - Præ-trænede danske modeller
   
2. Forbedringer:
   - Større dansk datasæt
   - Bedre prompt engineering
   - Evaluering af model performance 