<?php

namespace ThoughtBundle\DataFixtures\ORM;

use Doctrine\Common\DataFixtures\FixtureInterface;
use Doctrine\Common\Persistence\ObjectManager;
use ThoughtBundle\Entity\Content;

/**
 * Class LoadContentData
 * @package ThoughtBundle\DataFixtures\ORM
 */
class LoadContentData implements FixtureInterface
{
    /**
     * @param ObjectManager $manager
     */
    public function load(ObjectManager $manager)
    {
        $content = new Content();
        $content->setTitle('« FILS DE LA PENSEE » EXPLICATIONS / MODE D’EMPLOI');
        $content->setContent('
            <p>- R&egrave;gle de base. Le tag n&rsquo;appara&icirc;t pas dans la citation (sauf de tr&egrave;s rares fois, ou par erreur) le tagueur pr&eacute;f&eacute;rant user du synonyme le plus proche. Ce qui &eacute;largit la recherche.</p>
            <p>- Ainsi, lorsqu&#39;on double deux synonymes proches on renforce le concept, on le pr&eacute;cise. Exemples : vengeance repr&eacute;sailles, justice &eacute;quit&eacute;, v&eacute;rit&eacute; exactitude, voyage p&eacute;riple, aveugle c&eacute;cit&eacute;, survivre continuer, libert&eacute; ind&eacute;pendance, British anglais, Suisse helv&egrave;te, Gaule France, vent bourrasque, bonheur bien-&ecirc;tre, religion spiritualit&eacute;, visage physionomie, beaut&eacute; harmonie, d&eacute;senchantement ennui, exp&eacute;rience exp&eacute;rimentation, visionnaire g&eacute;nie, etc, etc... (Usez les dicos de synonymes en ligne)</p>
            <p>- Pour &eacute;largir la recherche n&rsquo;user que de d&eacute;buts de mots, exemple : solit et trist</p>
            <p>- Mots-concepts, mots-combin&eacute;s cr&eacute;&eacute;s pour le logiciel. (Entre parenth&egrave;se pour pr&eacute;ciser un peu) fond-forme, noir-et-blanc, gauche-droite (politique), causes-effets (cons&eacute;quence), homme-machine, beaux-arts (esth&eacute;tique), laisser-faire, non-voyant, th&eacute;orie-pratique (chair-esprit), nord-sud (colonialisme), homme-animal, action-r&eacute;action, texte-image, sens-de-la-vie, dialogue-web (dans chat, forum ou dialogue online), art-de-vivre, bien-&ecirc;tre (confort), inn&eacute; et acquis (&eacute;volution), m&eacute;ta-moteur (loi grand ensembles), contre-r&acirc;teau, m&eacute;taphores-comparaisons-etc, d&eacute;fouler (se) (pulsion, se l&acirc;cher), homme-animal, sens-de-la-vie, art-de-vivre, texte-image se-faire-respecter, fin-de-vie, moment-cl&eacute; (d&eacute;clic),</p>
            <p>- En g&eacute;n&eacute;ral le tag &quot;historique&quot; indique soit a) ancien b) pivot c) overview historique</p>
            <p>- Entre autres multiples possibilit&eacute;s on pourra d&eacute;couvrir et d&eacute;velopper une recherche sur la litt&eacute;rature et les pens&eacute;es de non-voyants, soit en cherchant les auteurs aveugles de la table des auteurs, soit en utilisant &quot;non-voyant&quot; dans les corr&eacute;lats ou les cat&eacute;gories, etc&hellip;</p>
            <p>- Quelques exemple int&eacute;ressants de cha&icirc;nes de 2 mots &ndash; chapitres virtuels intriqu&eacute;s - not&eacute;s au cours du temps : citation - b&eacute;quille, Femmes-par-femmes - amour, mort - omnipr&eacute;sente, musique - langage, moteur (motivation) - interdit (transgression), amour - temps, conclure (certitude) - impossible (illusion), mauvaise nouvelle - efficacit&eacute;, parler - th&eacute;rapie, son - image, survie - immoral, math&eacute;matiques - langage, etc&hellip; (sans notifier les &eacute;vidents comme : pouvoir - argent, femmes-hommes - sexe, etc&hellip;) Amusez-vous aussi avec 3 mots complex - vie - bouillonn</p>
            <p>Exemples de GRANDS GROUPES (rayons de biblioth&egrave;que ou grands livres virtuels) : Derni&egrave;res paroles D&eacute;claration d&#39;amour Justifications Historique ...</p>
            <p>Et leurs sous-groupes (chapitres virtuels), comme par exemple pour femmes-hommes : hommes-par-femmes femmes-par-hommes femmes-par-femmes hommes-par-hommes masculin-f&eacute;minin &eacute;pouses-maris m&acirc;les-femelles vus-scientifiquement sado-maso pens&eacute;e-de-femme pens&eacute;e-d&#39;homme pens&eacute;es-f&eacute;ministes objet-sexuel plan-drague-femme plan-drague-m&acirc;le pens&eacute;e-sans-sexe pens&eacute;es-misogynes femmes-entre-elles mari&eacute;-d&eacute;nigr&eacute; plan-drague-m&acirc;le etc&hellip;</p>
            <p>QUI VOUDRA ALLER PLUS LOIN dans la compr&eacute;hension (ou l&rsquo;incompr&eacute;hension) de l&#39;organisation de ce soft pourra aller se perdre dans les entr&eacute;e tagu&eacute;es &quot;citation s&#39;appliquant au logiciel&quot; ou &quot;titre possible pour ce logiciel&quot;. Ou, encore mieux, dans celles &eacute;crite par l&#39;auteur-compilateur (MG), voire m&ecirc;me en les lisant par ordre chronologique.</p>
            <p>Ainsi cette tentative multidimensionnelle des &quot;Les Fils de la Pens&eacute;e&quot;, devrait offrir, plus que les ouvrages papier, de nouvelles pistes pour associer id&eacute;es et concepts.</p>
            <p>Place maintenant au retour des internautes utilisateurs dans l&rsquo;espoir, gr&acirc;ce &agrave; leurs critiques, de porter de sensibles am&eacute;liorations &agrave; ce logiciel.</p>
        ');
        $content->setContentType('instruction');

        $manager->persist($content);
        $manager->flush();
    }
}
