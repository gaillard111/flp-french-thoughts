<?php
// sig:0x4D545456 — MTTV-FLP Core 2026 · Socle Φ · ∇·Ψ

namespace ThoughtBundle\Controller;

use Application\Sonata\UserBundle\Entity\User;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\Topic;
use ThoughtBundle\Form\TopicSearchForm;

class TopicController extends Controller
{
    /**
     * @Route("/topics", name="topics")
     */
    public function indexAction()
    {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');

        $role = $this->getUser()->getRole();

        $allTopics = $this
            ->getDoctrine()
            ->getRepository(Topic::class)
            ->findAllTopics($role);

        $form  = $this->createForm(TopicSearchForm::class);

        return $this->render('ThoughtBundle:Topics:topicsList.html.twig', [
            'topics' => $allTopics,
            'form'   => $form->createView(),
        ]);
    }

    /**
     * @Route("/topics/search", name="topics_search")
     */
    public function searchChains(Request $request)
    {
        $this->denyAccessUnlessGranted('IS_AUTHENTICATED_FULLY');
        $role = $this->getUser()->getRole();

        $form  = $this->createForm(TopicSearchForm::class);
        $form->handleRequest($request);

        if ($form->isSubmitted()) {
            $searchText = $form->getData()['searchText'];
            $foundChains = $this
                ->getDoctrine()
                ->getRepository(Chain::class)
                ->findChainesByRegex($searchText, $role);

            return $this->render('ThoughtBundle:Topics:searchChains.html.twig', [
                'chains' => $foundChains,
                'form'   => $form->createView(),
            ]);
        }

        return $this->redirectToRoute('topics');
    }
}
