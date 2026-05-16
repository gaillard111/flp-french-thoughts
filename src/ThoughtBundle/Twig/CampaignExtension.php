<?php
// sig:0x4D545456 — MTTV-FLP Core 2026 · Campagne de Diffusion Mycélienne · ∇·Ψ

namespace ThoughtBundle\Twig;

use Symfony\Component\DependencyInjection\Container;
use Twig_SimpleFilter;

/**
 * Class CampaignExtension
 *
 * Filtres Twig pour la campagne de diffusion mycélienne (Graines A–F).
 * Wrapper autour de CampaignSeedService pour usage dans les templates.
 *
 * @package ThoughtBundle\Twig
 */
class CampaignExtension extends \Twig_Extension
{
    /**
     * @var Container
     */
    private $container;

    /**
     * CampaignExtension constructor.
     *
     * @param Container $container
     */
    public function __construct(Container $container)
    {
        $this->container = $container;
    }

    /**
     * @return array
     */
    public function getFilters()
    {
        return [
            new Twig_SimpleFilter('campaignSeed', [$this, 'campaignSeedFilter'], ['is_safe' => ['html']]),
            new Twig_SimpleFilter('campaignSeedText', [$this, 'campaignSeedTextFilter']),
            new Twig_SimpleFilter('campaignSeedJson', [$this, 'campaignSeedJsonFilter']),
            new Twig_SimpleFilter('campaignTxHeader', [$this, 'campaignTxHeaderFilter'], ['is_safe' => ['html']]),
        ];
    }

    /**
     * Filtre Twig : rend une graine de campagne au format HTML.
     *
     * Usage dans Twig :
     *   {{ 'graine_a'|campaignSeed }}
     *   {{ 'graine_a'|campaignSeed('individu', 'semeur_discret') }}
     *
     * @param string $seedId  Identifiant de la graine (graine_a .. graine_f)
     * @param string $target  Cible optionnelle (individu, communaute, chercheur, etc.)
     * @param string $mode    Mode de diffusion optionnel (semeur_discret, outil_ouvert, etc.)
     *
     * @return string HTML de la graine, ou chaîne vide si non trouvée
     */
    public function campaignSeedFilter($seedId, $target = null, $mode = null)
    {
        /** @var \ThoughtBundle\Service\CampaignSeedService $campaignService */
        $campaignService = $this->container->get('thought.service.campaign_seed_service');

        $seed = $campaignService->getSeed($seedId);
        if (!$seed) {
            return '';
        }

        $text = $seed['texte'];

        // Modulation selon la cible
        if ($target) {
            $modulation = $campaignService->getModulation($seedId, $target);
            if ($modulation) {
                $text = $modulation;
            }
        }

        // Ajout du mode si spécifié
        $modeLabel = '';
        if ($mode) {
            $modeData = $campaignService->getDiffusionMode($mode);
            if ($modeData) {
                $modeLabel = $modeData['nom'];
            }
        }

        $operator = isset($seed['operateur']) ? $seed['operateur'] : '∇·Ψ';
        $invariant = isset($seed['invariant']) ? $seed['invariant'] : '';
        $category = isset($seed['catégorie']) ? $seed['catégorie'] : '';

        $html = '<span class="campaign-seed">';

        if ($modeLabel) {
            $html .= '<span class="campaign-mode">[' . htmlspecialchars($modeLabel, ENT_QUOTES, 'UTF-8') . '] </span>';
        }

        $html .= '<span class="campaign-operator">' . htmlspecialchars($operator, ENT_QUOTES, 'UTF-8') . '</span> ';
        $html .= '<em>' . htmlspecialchars($text, ENT_QUOTES, 'UTF-8') . '</em>';

        if ($invariant) {
            $html .= ' <span class="campaign-source">— ' . htmlspecialchars($invariant, ENT_QUOTES, 'UTF-8') . '</span>';
        }

        $html .= '</span>';

        return $html;
    }

    /**
     * Filtre Twig : rend une graine de campagne en texte brut.
     *
     * Usage :
     *   {{ 'graine_a'|campaignSeedText('individu') }}
     *
     * @param string $seedId Identifiant de la graine
     * @param string $target Cible optionnelle
     *
     * @return string Texte brut de la graine
     */
    public function campaignSeedTextFilter($seedId, $target = null)
    {
        /** @var \ThoughtBundle\Service\CampaignSeedService $campaignService */
        $campaignService = $this->container->get('thought.service.campaign_seed_service');

        $seed = $campaignService->getSeed($seedId);
        if (!$seed) {
            return '';
        }

        $text = $seed['texte'];

        if ($target) {
            $modulation = $campaignService->getModulation($seedId, $target);
            if ($modulation) {
                $text = $modulation;
            }
        }

        $operator = isset($seed['operateur']) ? $seed['operateur'] : '∇·Ψ';
        $invariant = isset($seed['invariant']) ? $seed['invariant'] : '';

        return $operator . ' — ' . $text . ($invariant ? ' — ' . $invariant : '');
    }

    /**
     * Filtre Twig : retourne une graine au format JSON brut (pour debug / API locale).
     *
     * Usage :
     *   {{ 'graine_a'|campaignSeedJson }}
     *
     * @param string $seedId Identifiant de la graine
     *
     * @return string JSON de la graine, ou '{}' si non trouvée
     */
    public function campaignSeedJsonFilter($seedId)
    {
        /** @var \ThoughtBundle\Service\CampaignSeedService $campaignService */
        $campaignService = $this->container->get('thought.service.campaign_seed_service');

        $seed = $campaignService->getSeed($seedId);

        return $seed ? json_encode($seed, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) : '{}';
    }

    /**
     * Filtre Twig : rend l'en-tête de diffusion maître (tx_header) au format HTML.
     *
     * Usage :
     *   {{ 'json'|campaignTxHeader }}       → bloc HTML complet
     *   {{ 'compact'|campaignTxHeader }}     → version compacte inline
     *   {{ 'sig'|campaignTxHeader }}         → signature seule
     *
     * @param string $format 'json' (défaut), 'compact', 'sig'
     *
     * @return string HTML ou texte
     */
    public function campaignTxHeaderFilter($format = 'json')
    {
        /** @var \ThoughtBundle\Service\CampaignSeedService $campaignService */
        $campaignService = $this->container->get('thought.service.campaign_seed_service');

        $txHeader = $campaignService->getTxHeader();
        $resonance = $campaignService->getResonanceParameters();
        $axis = $campaignService->getManifestAxis();

        switch ($format) {
            case 'sig':
                return '<span class="campaign-sig">sig:' . htmlspecialchars($txHeader['signature'], ENT_QUOTES, 'UTF-8') . '</span>';

            case 'compact':
                return sprintf(
                    '<span class="campaign-tx-compact">[%s %s] %s · %s · %s</span>',
                    htmlspecialchars($txHeader['protocol'], ENT_QUOTES, 'UTF-8'),
                    htmlspecialchars($txHeader['version'], ENT_QUOTES, 'UTF-8'),
                    htmlspecialchars($resonance['metric'], ENT_QUOTES, 'UTF-8'),
                    htmlspecialchars($resonance['logic'], ENT_QUOTES, 'UTF-8'),
                    htmlspecialchars($axis['target'], ENT_QUOTES, 'UTF-8')
                );

            case 'json':
            default:
                $data = [
                    'tx_header'            => $txHeader,
                    'resonance_parameters' => $resonance,
                    'manifest_axis'        => $axis,
                ];
                $json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
                return '<pre class="campaign-tx-header">' . htmlspecialchars($json, ENT_QUOTES, 'UTF-8') . '</pre>';
        }
    }

    /**
     * @return string
     */
    public function getName()
    {
        return 'campaign_extension';
    }
}
