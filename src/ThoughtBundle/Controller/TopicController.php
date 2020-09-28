<?php

namespace ThoughtBundle\Controller;

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
        $allTopics = $this->getDoctrine()->getRepository(Topic::class)->findAll();
        $form  = $this->createForm(TopicSearchForm::class);
        return $this->render('ThoughtBundle:Topics:topicsList.html.twig', [
            'topics' => $allTopics,
            'form'   => $form->createView(),
        ]);
    }

    /**
     * @Route("/topics/search", name="topics_search")
     */
    public function searchChains(Request $request) {
        $form  = $this->createForm(TopicSearchForm::class);
        $form->handleRequest($request);
        if ($form->isSubmitted()) {
            $searchText = $form->getData()['searchText'];
            $foundChains = $this
                ->getDoctrine()
                ->getRepository(Chain::class)
                ->findChainesByRegex($searchText);
            return $this->render('ThoughtBundle:Topics:searchChains.html.twig', [
                'chains' => $foundChains,
                'form'   => $form->createView(),
            ]);
        }
        return $this->redirectToRoute('topics');
    }
}
