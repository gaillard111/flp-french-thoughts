<?php

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
        $student = false;
        if ($this->isGranted(User::ROLE_STUDENT)) {
            $student = true;
        }

        $allTopics = $this
            ->getDoctrine()
            ->getRepository(Topic::class)
            ->findAllTopics($student);

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

        $student = false;
        if ($this->isGranted(User::ROLE_STUDENT)) {
            $student = true;
        }

        $form  = $this->createForm(TopicSearchForm::class);
        $form->handleRequest($request);
        if ($form->isSubmitted()) {
            $searchText = $form->getData()['searchText'];
            $foundChains = $this
                ->getDoctrine()
                ->getRepository(Chain::class)
                ->findChainesByRegex($searchText, $student);
            return $this->render('ThoughtBundle:Topics:searchChains.html.twig', [
                'chains' => $foundChains,
                'form'   => $form->createView(),
            ]);
        }
        return $this->redirectToRoute('topics');
    }
}
