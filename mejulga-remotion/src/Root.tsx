import React from 'react';
import {Composition} from 'remotion';
import {Minimalista} from './compositions/Minimalista';
import {Tribunal} from './compositions/Tribunal';
import type {RoteiroProps} from './types';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			<Composition
				id="Minimalista"
				component={Minimalista}
				durationInFrames={300}
				fps={30}
				width={1080}
				height={1920}
				defaultProps={{
					roteiro: {
						categoria: 'dinheiro',
						conclusao: 'Sem defesa possível.',
						cenas: [
							{numero: 1, texto: 'Você parcela até o pão na padaria?', duracao_segundos: 4},
							{numero: 2, texto: 'Chega aqui quem divide cafezinho em três...', duracao_segundos: 4},
							{numero: 3, texto: 'E ainda acha que tá fazendo investimento...', duracao_segundos: 4},
							{numero: 4, texto: 'Spoiler: juros não é seu amigo secreto.', duracao_segundos: 4},
							{numero: 5, texto: 'Diagnóstico: dependência crônica de parcelamento.', duracao_segundos: 4},
						],
					},
					audioSrc: 'audio/dinheiro_audio.mp3',
				} satisfies RoteiroProps}
			/>
			<Composition
				id="Tribunal"
				component={Tribunal}
				durationInFrames={300}
				fps={30}
				width={1080}
				height={1920}
				defaultProps={{
					roteiro: {
						categoria: 'dinheiro',
						conclusao: 'Sem defesa possível.',
						cenas: [
							{numero: 1, texto: 'Você parcela até o pão na padaria?', duracao_segundos: 4},
							{numero: 2, texto: 'Chega aqui quem divide cafezinho em três...', duracao_segundos: 4},
							{numero: 3, texto: 'E ainda acha que tá fazendo investimento...', duracao_segundos: 4},
							{numero: 4, texto: 'Spoiler: juros não é seu amigo secreto.', duracao_segundos: 4},
							{numero: 5, texto: 'Diagnóstico: dependência crônica de parcelamento.', duracao_segundos: 4},
						],
					},
					audioSrc: 'audio/dinheiro_audio.mp3',
				} satisfies RoteiroProps}
			/>
		</>
	);
};
