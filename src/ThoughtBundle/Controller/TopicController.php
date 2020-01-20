<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Topic;
use ThoughtBundle\Form\TopicSearchForm;

class TopicController extends Controller
{
    /**
     * @Route("/topics/{topicId}", name="topic_page", requirements={"topicId"="\d+"})
     */
    public function indexAction(Request $request)
    {
        $topicId = $request->get('topicId');
        $em      = $this->getDoctrine()->getManager();
        $topic   = $em->getRepository(Topic::class)->find($topicId);

        return $this->render('@Thought/Topic/topicPage.html.twig', [
            'topic' => $topic,
        ]);
    }

    /**
     * @Route("/topics", name="all_topics")
     *
     * @param Request $request
     *
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function AllAction(Request $request)
    {
        $em = $this->get('doctrine.orm.entity_manager');

        $topics = $em->getRepository(Topic::class)->findAll();

        $topic = new Topic();
        $form  = $this->createForm(TopicSearchForm::class, $topic);
        $form->handleRequest($request);

        if ($form->isSubmitted()) {
            $topic  = $form->getData();
            $topics = $em->getRepository(Topic::class)->searchTopics($topic);

            return $this->render('ThoughtBundle:Topic:list.html.twig', [
                'topics' => $topics,
                'form'   => $form->createView(),
            ]);
        }

        return $this->render('ThoughtBundle:Topic:list.html.twig', [
            'topics' => $topics,
            'form'   => $form->createView(),
        ]);
    }
}
