/** WCAG 2.x relative luminance and contrast ratio, from any CSS rgb()/hex color string. */

function parse(color: string): [number, number, number] | null {
  const c = color.trim()
  const hex = c.match(/^#([0-9a-f]{6})$/i)
  if (hex) {
    const n = parseInt(hex[1]!, 16)
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
  }
  const rgb = c.match(/^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/i)
  if (rgb) return [Number(rgb[1]), Number(rgb[2]), Number(rgb[3])]
  return null
}

function luminance([r, g, b]: [number, number, number]) {
  const lin = (v: number) => {
    const s = v / 255
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
  }
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
}

export function contrastRatio(a: string, b: string): number | null {
  const pa = parse(a)
  const pb = parse(b)
  if (!pa || !pb) return null
  const la = luminance(pa)
  const lb = luminance(pb)
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05)
}

export function toHex(color: string): string {
  const p = parse(color)
  if (!p) return color
  return '#' + p.map((v) => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase()
}
