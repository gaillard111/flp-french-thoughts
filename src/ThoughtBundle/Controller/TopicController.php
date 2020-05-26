<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
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
     * @return Response
     */
    public function AllAction(Request $request)
    {
        $em = $this->get('doctrine.orm.entity_manager');

        $topics = $em->getRepository(Topic::class)->searchTopics();

        $topic = new Topic();
        $form  = $this->createForm(TopicSearchForm::class, $topic);
        $form->handleRequest($request);

        if ($form->isSubmitted()) {
            $query  = true;
            $topic  = $form->getData();
            $topics = $em->getRepository(Topic::class)->searchTopics($topic);

            return $this->render('ThoughtBundle:Topic:list.html.twig', [
                'query'  => $query,
                'topics' => $topics,
                'form'   => $form->createView(),
            ]);
        }

        $query = false;
        return $this->render('ThoughtBundle:Topic:list.html.twig', [
            'query'  => $query,
            'topics' => $topics,
            'form'   => $form->createView(),
        ]);
    }
}
