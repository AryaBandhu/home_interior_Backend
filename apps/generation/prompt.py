ROOM_TYPES = {
    'living-room': 'living room',
    'bedroom': 'bedroom',
    'kitchen': 'kitchen',
    'bathroom': 'bathroom',
    'dining-room': 'dining room',
    'home-office': 'home office',
    'kids-room': 'kids room',
    'balcony': 'balcony',
}

DESIGN_STYLES = {
    'modern': 'modern interior design with clean geometric lines, sleek low-profile furniture, premium materials like marble and glass, recessed and pendant lighting, and sophisticated contemporary décor',
    'minimalist': 'minimalist interior design with intentionally curated clutter-free spaces, essential furniture only, monochromatic soft textures, hidden storage, and serene functional elegance',
    'scandinavian': 'Scandinavian interior design featuring light-toned natural wood, abundant natural and warm artificial lighting, hygge-inspired cozy textiles, and beautifully simple functional furniture',
    'industrial': 'industrial interior design with raw exposed brick walls, concrete surfaces, black metal framework and accents, Edison bulb lighting, weathered wood, and urban loft aesthetics',
    'bohemian': 'bohemian interior design with richly layered textiles and patterns, eclectic artistic décor, macramé and rattan, lush indoor plants, vintage rugs, and warm inviting textures',
    'traditional': 'traditional interior design with ornate carved wood furniture, decorative crown moldings, rich fabric upholstery, classic symmetrical arrangements, and timeless elegant décor',
    'contemporary': 'contemporary interior design with current trending elements, sculptural refined furniture, high-end finishes, bold art pieces, and harmoniously balanced aesthetics',
    'mid-century-modern': 'mid-century modern interior design with organic curved wooden furniture, iconic tapered legs, retro color pops, geometric patterns, and effortlessly clean lines',
    'japanese': 'Japanese-inspired interior design with Zen minimalism, shoji screen elements, natural bamboo and wood, soft diffused lighting, tatami textures, and tranquil peaceful atmosphere',
    'rustic': 'rustic interior design featuring heavy reclaimed barn wood, natural stone accent walls, wrought iron fixtures, cozy fireplace warmth, and handcrafted artisanal elements',
}

COLOR_THEMES = {
    'neutral': 'a neutral color palette with warm white walls, soft beige upholstery, ivory accents, light gray textiles, and natural wood tones throughout',
    'warm': 'a warm color palette with creamy walls, sandy beige base, terracotta accent pieces, rich caramel leather, and honey-toned warm wood',
    'cool': 'a cool color palette with crisp white base, steel gray furniture, ocean blue accents, muted sage green textiles, and brushed silver hardware',
    'earth-tones': 'an earth-tone color palette with olive green walls, terracotta clay accents, rich chocolate brown furniture, natural stone gray, and raw wood elements',
    'monochrome': 'a monochrome color palette with dramatic contrast between pure black, bright white, varying shades of gray, and deep charcoal accents',
    'pastel': 'a soft pastel color palette with blush pink textiles, mint green accents, powder blue walls, gentle lavender touches, and warm cream base',
    'bold-vibrant': 'a bold vibrant color palette with deep royal blue, rich emerald green accents, warm mustard yellow, living coral touches, and dramatic striking contrasts',
    'dark-moody': 'a dark moody color palette with deep charcoal walls, matte black fixtures, rich walnut wood, navy blue textiles, and forest green velvet accents',
}

ROOM_SIZES = {
    'small': 'maximizing space efficiency with compact multi-functional furniture, clever built-in storage solutions, bright reflective surfaces, mirrors for depth, and maintaining an open airy spacious feel',
    'medium': 'maintaining well-balanced furniture proportions with comfortable walking circulation paths, practical zoned layout, and a mix of statement and functional pieces',
    'large': 'utilizing the generous spacious layout with appropriately scaled larger furniture, layered ambient and task lighting, curated premium decorative elements, and defined activity zones',
    'extra-large': 'creating a luxurious grand interior with impressive statement furniture pieces, expansive open layouts, multiple distinct functional zones, architectural premium finishes, and resort-like sophistication',
}

PROMPT_TEMPLATE = (
    "Redesign this {room_type} as a {design_style}. "
    "Apply {color_theme}. "
    "Optimize for a {room_size} space by {room_size_desc}. "
    "CRITICAL: Preserve the exact room structure — same wall positions, door locations, window placements, ceiling height, floor area, room shape, and architectural proportions from the original image. "
    "Do NOT change the camera angle, perspective, or room dimensions. "
    "Replace all furniture, soft furnishings, lighting fixtures, wall treatments, décor items, and accessories with high-end designer elements that perfectly match the selected style and color palette. "
    "Render with photorealistic quality: accurate material textures (fabric weave, wood grain, metal reflections, stone veining), physically correct soft natural lighting with gentle shadows, "
    "proper depth of field, and professional interior photography composition. "
    "The final image must look like a real photograph taken by a professional interior photographer for an architecture magazine."
)


def build_prompt(room_type_slug, design_style_slug, color_theme_slug, room_size_slug):
    return PROMPT_TEMPLATE.format(
        room_type=ROOM_TYPES.get(room_type_slug, room_type_slug),
        design_style=DESIGN_STYLES.get(design_style_slug, design_style_slug),
        color_theme=COLOR_THEMES.get(color_theme_slug, color_theme_slug),
        room_size=room_size_slug,
        room_size_desc=ROOM_SIZES.get(room_size_slug, 'optimizing the space'),
    )
