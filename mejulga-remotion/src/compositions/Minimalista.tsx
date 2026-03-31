import React from 'react';
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

const ROXO_ESCURO = '#2D1060';
const ROXO_MEDIO  = '#6D44B8';
const ROXO_CLARO  = '#A855F7';
const ROXO_BG     = '#FAF8FF';
const ROXO_LINHA  = '#E9D5FF';
const BRANCO      = '#FFFFFF';

const LinhaAnimada: React.FC<{delay?: number}> = ({delay = 0}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({frame: frame - delay, fps, config: {damping: 20, stiffness: 80}});
	return (
		<div style={{width: progress * 300, height: 3, backgroundColor: ROXO_CLARO, borderRadius: 2}} />
	);
};

const TextoEntrada: React.FC<{children: React.ReactNode; delay?: number; style?: React.CSSProperties}> = ({children, delay = 0, style = {}}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({frame: frame - delay, fps, config: {damping: 18, stiffness: 60}});
	const opacity = interpolate(frame - delay, [0, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<div style={{transform: `translateY(${(1 - progress) * 40}px)`, opacity, ...style}}>
			{children}
		</div>
	);
};

const BulletCena: React.FC<{texto: string; delay: number}> = ({texto, delay}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const progress = spring({frame: frame - delay, fps, config: {damping: 22, stiffness: 70}});
	const opacity = interpolate(frame - delay, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	return (
		<div style={{display: 'flex', alignItems: 'flex-start', gap: 20, opacity, transform: `translateX(${(1 - progress) * -30}px)`, marginBottom: 28}}>
			<div style={{width: 8, height: 8, borderRadius: '50%', backgroundColor: ROXO_CLARO, marginTop: 16, flexShrink: 0}} />
			<p style={{fontFamily: 'sans-serif', fontSize: 36, color: ROXO_MEDIO, margin: 0, lineHeight: 1.4, fontWeight: 400}}>
				{texto}
			</p>
		</div>
	);
};

export const Minimalista: React.FC<RoteiroProps> = ({roteiro, audioSrc}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const {cenas, conclusao} = roteiro;

	const veredictoProgress = spring({frame: frame - 20, fps, config: {damping: 14, stiffness: 50}});
	const veredictoOpacity = interpolate(frame - 20, [0, 15], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const ctaOpacity = interpolate(frame - 50, [0, 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const ctaProgress = spring({frame: frame - 50, fps, config: {damping: 20, stiffness: 60}});

	return (
		<AbsoluteFill style={{backgroundColor: ROXO_BG, fontFamily: 'sans-serif'}}>
			<Audio src={staticFile(audioSrc)} />
			<div style={{position: 'absolute', left: 0, top: 0, width: 12, height: '100%', backgroundColor: ROXO_CLARO}} />
			<div style={{position: 'absolute', right: 0, top: 0, width: 12, height: '100%', backgroundColor: ROXO_CLARO}} />

			<div style={{position: 'absolute', inset: 0, paddingLeft: 80, paddingRight: 80, display: 'flex', flexDirection: 'column', paddingTop: 120}}>
				<TextoEntrada delay={0}>
					<p style={{fontSize: 52, fontWeight: 700, color: ROXO_ESCURO, margin: 0, textAlign: 'center', letterSpacing: 4}}>ME JULGA</p>
				</TextoEntrada>
				<TextoEntrada delay={5}>
					<p style={{fontSize: 30, fontWeight: 300, color: ROXO_MEDIO, margin: '8px 0 0', textAlign: 'center', letterSpacing: 2}}>com a Dra. Julga</p>
				</TextoEntrada>

				<div style={{display: 'flex', justifyContent: 'center', marginTop: 30, marginBottom: 30}}>
					<LinhaAnimada delay={10} />
				</div>

				<div style={{backgroundColor: BRANCO, borderRadius: 32, padding: '52px 60px', border: `3px solid ${ROXO_LINHA}`, marginBottom: 44, transform: `scale(${0.88 + veredictoProgress * 0.12})`, opacity: veredictoOpacity}}>
					<p style={{fontSize: 26, color: ROXO_CLARO, margin: '0 0 20px', textAlign: 'center', letterSpacing: 3, textTransform: 'uppercase'}}>─── Veredicto Final ───</p>
					<p style={{fontSize: conclusao.length > 40 ? 70 : 86, fontWeight: 700, color: ROXO_ESCURO, margin: 0, textAlign: 'center', lineHeight: 1.2}}>{conclusao}</p>
				</div>

				<div style={{marginBottom: 44}}>
					<p style={{fontSize: 26, color: ROXO_CLARO, margin: '0 0 24px', letterSpacing: 2, textAlign: 'center'}}>A história completa está no áudio ▶</p>
					{cenas.slice(0, 5).map((cena, i) => (
						<BulletCena key={cena.numero} texto={cena.texto} delay={28 + i * 12} />
					))}
				</div>

				<div style={{backgroundColor: ROXO_ESCURO, borderRadius: 28, padding: '48px 48px', textAlign: 'center', opacity: ctaOpacity, transform: `translateY(${(1 - ctaProgress) * 60}px)`}}>
					<p style={{fontSize: 44, fontWeight: 700, color: BRANCO, margin: '0 0 12px'}}>Descobre o seu em</p>
					<p style={{fontSize: 40, fontWeight: 400, color: ROXO_CLARO, margin: 0}}>mejulga.com.br</p>
				</div>

				<p style={{fontSize: 28, color: ROXO_MEDIO, textAlign: 'center', marginTop: 36, letterSpacing: 2}}>@dra.julga  •  ME JULGA</p>
			</div>
		</AbsoluteFill>
	);
};
