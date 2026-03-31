export type Cena = {
	numero: number;
	texto: string;
	duracao_segundos: number;
};

export type Roteiro = {
	categoria: string;
	conclusao: string;
	cenas: Cena[];
};

export type RoteiroProps = {
	roteiro: Roteiro;
	audioSrc: string;
};
