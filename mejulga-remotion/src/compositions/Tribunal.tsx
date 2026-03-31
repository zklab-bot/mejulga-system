import {
	AbsoluteFill,
	Audio,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
	staticFile,
} from 'remotion';
import type {RoteiroProps} from '../types';

const BG_ESCURO     = '#080514';
const ROXO_PROFUNDO = '#150930';
const ROXO_VIBRANTE = '#7C3AED';
const ROXO_CLARO    = '#A78BFA';
const ROXO_NEON     = '#C4B5FD';
const DOURADO       = '#D4AF37';
const DOURADO_CLARO = '#F0D060';
const BRANCO        = '#FFFFFF';
const VERMELHO      = '#EF4444';

const TextoEntrada: React.FC<{
	children: React.ReactNode;
	delay?: number;
	style?: React.CSSProperties;
}> = ({children, delay = 0, style = {}}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({frame: frame - delay, fps, config: {damping: 18, stiffness: 60}});
	const opacity = interpolate(frame - delay, [0, 12], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div style={{transform: `translateY(${(1 - progress) * 40}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

const LinhaAcusacao: React.FC<{texto: string; delay: number; index: number}> = ({
	texto,
	delay,
	index,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({frame: frame - delay, fps, config: {damping: 22, stiffness: 65}});
	const opacity = interpolate(frame - delay, [0, 10], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const cores = [ROXO_CLARO, ROXO_NEON, DOURADO_CLARO, ROXO_CLARO, ROXO_NEON];
	const cor = cores[index % cores.length];

	return (
		<div
			style={{
				display: 'flex',
				alignItems: 'flex-start',
				gap: 24,
				opacity,
				transform: `translateX(${(1 - progress) * -50}px)`,
				marginBottom: 28,
				paddingLeft: 28,
				borderLeft: `4px solid ${cor}`,
			}}
		>
			<p style={{
				fontFamily: 'sans-serif',
				fontSize: 36,
				color: cor,
				margin: 0,
				lineHeight: 1.45,
				fontWeight: 300,
				letterSpacing: 0.5,
			}}>
				{texto}
			</p>
		</div>
	);
};

const Carimbo: React.FC<{delay: number}> = ({delay}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({frame: frame - delay, fps, config: {damping: 8, stiffness: 200, mass: 0.6}});
	const opacity = interpolate(frame - delay, [0, 3], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	return (
		<div
			style={{
				opacity,
				transform: `scale(${progress}) rotate(-8deg)`,
				display: 'inline-block',
				border: `8px solid ${VERMELHO}`,
				borderRadius: 12,
				padding: '16px 48px',
				position: 'absolute',
				top: 40,
				right: 60,
			}}
		>
			<p style={{
				fontSize: 72,
				fontWeight: 900,
				color: VERMELHO,
				margin: 0,
				letterSpacing: 6,
				textTransform: 'uppercase',
				lineHeight: 1,
				fontFamily: 'sans-serif',
			}}>
				CULPADE
			</p>
		</div>
	);
};

export const Tribunal: React.FC<RoteiroProps> = ({roteiro, audioSrc}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const {cenas, conclusao} = roteiro;

	const headerOpacity = interpolate(frame, [0, 20], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const headerProgress = spring({frame, fps, config: {damping: 20, stiffness: 50}});

	const veredictoDelay = 25;
	const veredictoOpacity = interpolate(frame - veredictoDelay, [0, 20], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const veredictoProgress = spring({
		frame: frame - veredictoDelay,
		fps,
		config: {damping: 16, stiffness: 55},
	});

	const ctaDelay = 55;
	const ctaOpacity = interpolate(frame - ctaDelay, [0, 20], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const ctaProgress = spring({frame: frame - ctaDelay, fps, config: {damping: 20, stiffness: 60}});

	return (
		<AbsoluteFill style={{backgroundColor: BG_ESCURO, fontFamily: 'sans-serif', overflow: 'hidden'}}>
			<Audio src={staticFile(audioSrc)} />

			{/* Gradiente radial de fundo */}
			<div style={{
				position: 'absolute',
				inset: 0,
				background: `radial-gradient(ellipse 80% 50% at 50% -10%, ${ROXO_PROFUNDO}, transparent)`,
			}} />

			{/* Grid de linhas decorativas */}
			{[...Array(10)].map((_, i) => (
				<div key={`h${i}`} style={{
					position: 'absolute', left: 0, right: 0,
					top: `${i * 11}%`, height: 1,
					backgroundColor: ROXO_VIBRANTE, opacity: 0.05,
				}} />
			))}
			{[...Array(7)].map((_, i) => (
				<div key={`v${i}`} style={{
					position: 'absolute', top: 0, bottom: 0,
					left: `${i * 17}%`, width: 1,
					backgroundColor: ROXO_VIBRANTE, opacity: 0.04,
				}} />
			))}

			{/* Barra dourada topo */}
			<div style={{
				position: 'absolute', top: 0, left: 0, right: 0, height: 6,
				background: `linear-gradient(90deg, transparent, ${DOURADO}, ${DOURADO_CLARO}, ${DOURADO}, transparent)`,
			}} />

			{/* Barra dourada rodapé */}
			<div style={{
				position: 'absolute', bottom: 0, left: 0, right: 0, height: 6,
				background: `linear-gradient(90deg, transparent, ${DOURADO}, ${DOURADO_CLARO}, ${DOURADO}, transparent)`,
			}} />

			<div style={{
				position: 'absolute', inset: 0,
				padding: '90px 80px',
				display: 'flex', flexDirection: 'column',
			}}>

				{/* ── HEADER ── */}
				<div style={{
					textAlign: 'center', marginBottom: 56,
					opacity: headerOpacity,
					transform: `translateY(${(1 - headerProgress) * -40}px)`,
				}}>
					<div style={{
						display: 'inline-flex',
						alignItems: 'center',
						gap: 24,
						border: `1px solid ${DOURADO}`,
						borderRadius: 10,
						padding: '18px 64px',
						marginBottom: 28,
					}}>
						<span style={{fontSize: 36, color: DOURADO}}>⚖</span>
						<p style={{
							fontSize: 30, color: DOURADO, margin: 0,
							letterSpacing: 6, fontWeight: 300, textTransform: 'uppercase',
						}}>
							Tribunal da Dra. Julga
						</p>
						<span style={{fontSize: 36, color: DOURADO}}>⚖</span>
					</div>

					{/* ON AIR badge */}
					<div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20}}>
						<div style={{flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${ROXO_VIBRANTE})`}} />
						<div style={{
							backgroundColor: VERMELHO,
							borderRadius: 6, padding: '8px 24px',
							display: 'flex', alignItems: 'center', gap: 10,
						}}>
							<div style={{
								width: 10, height: 10, borderRadius: '50%',
								backgroundColor: BRANCO, opacity: 0.9,
							}} />
							<p style={{
								fontSize: 22, color: BRANCO, margin: 0,
								fontWeight: 700, letterSpacing: 3,
							}}>ON AIR</p>
						</div>
						<div style={{flex: 1, height: 1, background: `linear-gradient(270deg, transparent, ${ROXO_VIBRANTE})`}} />
					</div>
				</div>

				{/* ── VEREDICTO ── */}
				<div style={{
					position: 'relative',
					backgroundColor: 'rgba(8, 5, 20, 0.9)',
					border: `2px solid ${ROXO_VIBRANTE}`,
					borderRadius: 20,
					padding: '44px 56px',
					marginBottom: 44,
					opacity: veredictoOpacity,
					transform: `translateY(${(1 - veredictoProgress) * 30}px)`,
				}}>
					{/* Carimbo CULPADE */}
					<Carimbo delay={veredictoDelay + 15} />

					<p style={{
						fontSize: 22, color: ROXO_NEON, margin: '0 0 20px',
						letterSpacing: 5, textAlign: 'center',
						textTransform: 'uppercase', fontWeight: 300,
					}}>
						▸  Veredicto Final  ◂
					</p>

					<p style={{
						fontSize: conclusao.length > 35 ? 68 : 82,
						fontWeight: 700, color: BRANCO,
						margin: 0, lineHeight: 1.2, textAlign: 'center',
					}}>
						{conclusao}
					</p>
				</div>

				{/* ── ACUSAÇÕES (cenas) ── */}
				<div style={{flex: 1, marginBottom: 40}}>
					<TextoEntrada delay={20}>
						<p style={{
							fontSize: 22, color: ROXO_CLARO,
							margin: '0 0 28px', letterSpacing: 4,
							textTransform: 'uppercase', fontWeight: 300,
						}}>
							Provas do processo:
						</p>
					</TextoEntrada>
					{cenas.slice(0, 5).map((cena, i) => (
						<LinhaAcusacao
							key={cena.numero}
							texto={cena.texto}
							delay={30 + i * 10}
							index={i}
						/>
					))}
				</div>

				{/* ── CTA ── */}
				<div style={{
					background: `linear-gradient(135deg, ${ROXO_VIBRANTE}, #5B21B6)`,
					borderRadius: 24, padding: '48px 56px',
					textAlign: 'center',
					opacity: ctaOpacity,
					transform: `translateY(${(1 - ctaProgress) * 60}px)`,
					border: `1px solid ${ROXO_CLARO}`,
				}}>
					<p style={{fontSize: 42, fontWeight: 700, color: BRANCO, margin: '0 0 12px'}}>
						E o seu diagnóstico?
					</p>
					<p style={{fontSize: 38, fontWeight: 400, color: ROXO_NEON, margin: 0}}>
						mejulga.com.br
					</p>
				</div>

				{/* Rodapé */}
				<p style={{
					fontSize: 26, color: ROXO_CLARO,
					textAlign: 'center', marginTop: 36,
					letterSpacing: 3, fontWeight: 300,
				}}>
					@dra.julga  •  ME JULGA
				</p>
			</div>
		</AbsoluteFill>
	);
};
