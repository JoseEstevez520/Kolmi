# Frontend

Web en Vue 3 + Vite, partiendo de la web del repo de clase.

## Estado

El código está traído como base, pero **no arranca tal cual**: importa el contenido de la
clase (los `.md` de `modulos/` y `extra/` por rutas relativas), y ese contenido no está aquí.
Antes de usarlo hay que adaptarlo:

- Sustituir los imports de contenido por las páginas propias de Kolmi.
- Ajustar `src/data/paginas.js` y el router a las pantallas de la app (login, dejar nota, mis
  notas).

## Arrancar

```bash
npm install
npm run dev
```

Necesita Node 20 o superior. El diseño y las reglas, en [`design.md`](design.md).
