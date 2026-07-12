import { Config } from "@remotion/cli/config";

// Prores 4444 сохраняет альфу — для оверлеев поверх видео в Premiere.
// Для сэмпла (mp4) альфа не нужна, но конфиг общий.
Config.setVideoImageFormat("png");
Config.overrideWebpackConfig((c) => c);
Config.setConcurrency(null); // авто по числу ядер
